from collections.abc import AsyncIterator, Callable
from io import BytesIO
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx
from PIL import Image

from appicon.clients import ITUNES_URL, ItunesClient
from appicon.models import AppInfo
from appicon.service import IconService

pytestmark = pytest.mark.anyio
type Recorded = Callable[[str], Any]

GOOGLE_ART = (
    "https://is1-ssl.mzstatic.com/image/thumb/Purple211/v4/72/33/d8/"
    "7233d884-35b3-1ed3-4376-b3888064295f/"
    "SuperG_ios26-0-0-1x_U007epad-0-0-0-1-0-0-sRGB-0-0-0-85-220.png"
)


def encode(size: tuple[int, int], fmt: str = "PNG") -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size).save(buffer, format=fmt)
    return buffer.getvalue()


@pytest.fixture
async def service() -> AsyncIterator[IconService]:
    async with httpx.AsyncClient() as http:
        yield IconService(ItunesClient(http, backoff=0), default_country="jp")


@pytest.fixture
def google(recorded: Recorded) -> AppInfo:
    return AppInfo.from_itunes(recorded("lookup_google_us.json")["results"][0], "us")


def mock_lookup(respx_mock: respx.MockRouter, recorded: Recorded, country: str) -> respx.Route:
    return respx_mock.get(
        f"{ITUNES_URL}/lookup", params={"id": "284815942", "country": country}
    ).respond(json=recorded("lookup_google_us.json"))


async def test_resolve_uses_the_country_in_the_link(
    service: IconService, respx_mock: respx.MockRouter, recorded: Recorded
) -> None:
    mock_lookup(respx_mock, recorded, "cn")

    app = await service.resolve("https://apps.apple.com/cn/app/google/id284815942")

    assert (app.track_id, app.country) == (284815942, "cn")


async def test_resolve_bare_id_uses_the_default_country(
    service: IconService, respx_mock: respx.MockRouter, recorded: Recorded
) -> None:
    mock_lookup(respx_mock, recorded, "jp")

    app = await service.resolve("284815942")

    assert app.country == "jp"


async def test_resolve_explicit_country_wins_over_the_link(
    service: IconService, respx_mock: respx.MockRouter, recorded: Recorded
) -> None:
    mock_lookup(respx_mock, recorded, "gb")

    app = await service.resolve("https://apps.apple.com/cn/app/id284815942", country="gb")

    assert app.country == "gb"


async def test_search_merges_storefronts_and_drops_duplicates(
    service: IconService, respx_mock: respx.MockRouter, recorded: Recorded
) -> None:
    for country in ("us", "cn"):
        respx_mock.get(f"{ITUNES_URL}/search", params={"country": country}).respond(
            json=recorded(f"search_google_{country}.json")
        )

    apps = await service.search("google", countries=["us", "cn"], limit=3)

    assert [(app.track_id, app.country) for app in apps] == [
        (284815942, "us"),
        (535886823, "us"),
        (422689480, "us"),
        (585027354, "cn"),
    ]


async def test_fetch_icon_requests_the_given_size_and_format(
    service: IconService, respx_mock: respx.MockRouter, google: AppInfo
) -> None:
    respx_mock.get(f"{GOOGLE_ART}/64x64bb.png").respond(content=b"thumb")

    assert await service.fetch_icon(google, 64) == b"thumb"


async def test_download_saves_the_original_icon_named_by_its_real_size(
    service: IconService, respx_mock: respx.MockRouter, google: AppInfo, tmp_path: Path
) -> None:
    original = encode((1024, 1024))
    respx_mock.get(f"{GOOGLE_ART}/10000x10000bb.png").respond(content=original)

    saved = await service.download(google, tmp_path)

    assert saved == tmp_path / "Google_447.9_1024x1024.png"
    assert saved.read_bytes() == original


async def test_download_honours_size_format_name_and_creates_the_folder(
    service: IconService, respx_mock: respx.MockRouter, google: AppInfo, tmp_path: Path
) -> None:
    respx_mock.get(f"{GOOGLE_ART}/64x64bb.jpg").respond(content=encode((64, 64), "JPEG"))

    saved = await service.download(google, tmp_path / "icons", size=64, fmt="jpg", name="G")

    assert saved == tmp_path / "icons" / "G_447.9_64x64.jpg"
    assert saved.exists()


async def test_download_writes_nothing_when_the_cdn_sends_no_image(
    service: IconService, respx_mock: respx.MockRouter, google: AppInfo, tmp_path: Path
) -> None:
    respx_mock.get(f"{GOOGLE_ART}/10000x10000bb.png").respond(content=b"<html>oops</html>")

    with pytest.raises(ValueError, match="not an image"):
        await service.download(google, tmp_path)
    assert list(tmp_path.iterdir()) == []
