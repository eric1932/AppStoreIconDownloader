"""Regression tests against the real iTunes API and artwork CDN.

Run with: uv run pytest -m network tests/regression
"""

from pathlib import Path

import pytest

from appicon.clients import ItunesClient, make_http_client
from appicon.service import IconService

pytestmark = [pytest.mark.network, pytest.mark.anyio]

GOOGLE_LINK = "https://apps.apple.com/us/app/google/id284815942"
GOOGLE_ID = 284815942
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


async def test_downloads_the_google_icon_at_full_size(tmp_path: Path) -> None:
    async with make_http_client() as http:
        service = IconService(ItunesClient(http))
        app = await service.resolve(GOOGLE_LINK)
        saved = await service.download(app, tmp_path)

    assert (app.track_id, app.name, app.bundle_id) == (
        GOOGLE_ID,
        "Google",
        "com.google.GoogleMobile",
    )
    assert saved.parent == tmp_path
    assert saved.name.startswith("Google_")
    assert saved.name.endswith("_1024x1024.png")
    assert saved.read_bytes().startswith(PNG_SIGNATURE)


async def test_search_finds_google_in_the_us_store() -> None:
    async with make_http_client() as http:
        apps = await IconService(ItunesClient(http)).search("google", ["us"], limit=5)

    assert GOOGLE_ID in [app.track_id for app in apps]
