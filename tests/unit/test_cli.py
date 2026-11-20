from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
import respx
from PIL import Image
from typer.testing import CliRunner

from appicon import __version__, preview
from appicon.cli import app
from appicon.clients import ITUNES_URL

type Recorded = Callable[[str], Any]
runner = CliRunner()
GOOGLE_LINK = "https://apps.apple.com/us/app/google/id284815942"
NO_RESULTS = {"resultCount": 0, "results": []}


def encode_png(size: tuple[int, int]) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size).save(buffer, format="PNG")
    return buffer.getvalue()


def art_dir(result: dict[str, Any]) -> str:
    """Folder part of a recorded artworkUrl512, e.g. ``https://.../SuperG.png``."""
    return str(result["artworkUrl512"]).rsplit("/", 1)[0]


@pytest.fixture(autouse=True)
def plain_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep iTerm2 previews out of the captured output."""
    monkeypatch.delenv("TERM_PROGRAM", raising=False)
    monkeypatch.delenv("LC_TERMINAL", raising=False)


@pytest.fixture
def google_art(recorded: Recorded) -> str:
    return art_dir(recorded("lookup_google_us.json")["results"][0])


def test_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == f"appicon {__version__}"


def test_get_saves_the_full_size_icon(
    respx_mock: respx.MockRouter, recorded: Recorded, google_art: str, tmp_path: Path
) -> None:
    respx_mock.get(f"{ITUNES_URL}/lookup", params={"id": "284815942", "country": "us"}).respond(
        json=recorded("lookup_google_us.json")
    )
    respx_mock.get(f"{google_art}/10000x10000bb.png").respond(content=encode_png((1024, 1024)))

    result = runner.invoke(app, ["get", GOOGLE_LINK, "-o", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert (tmp_path / "Google_447.9_1024x1024.png").is_file()
    assert "Google_447.9_1024x1024.png" in result.output


def test_get_dry_run_prints_the_icon_url_and_saves_nothing(
    respx_mock: respx.MockRouter, recorded: Recorded, google_art: str, tmp_path: Path
) -> None:
    respx_mock.get(f"{ITUNES_URL}/lookup").respond(json=recorded("lookup_google_us.json"))

    result = runner.invoke(
        app, ["get", "284815942", "--dry-run", "-s", "512", "-f", "jpg", "-o", str(tmp_path)]
    )

    assert result.exit_code == 0, result.output
    assert "https://apps.apple.com/us/app/id284815942" in result.output
    assert f"{google_art}/512x512bb.jpg" in result.output
    assert list(tmp_path.iterdir()) == []


def test_get_prompts_for_the_link_when_none_is_given(
    respx_mock: respx.MockRouter, recorded: Recorded
) -> None:
    respx_mock.get(f"{ITUNES_URL}/lookup", params={"id": "284815942"}).respond(
        json=recorded("lookup_google_us.json")
    )

    result = runner.invoke(app, ["get", "--dry-run"], input="284815942\n")

    assert result.exit_code == 0, result.output
    assert "Google" in result.output


def test_get_reports_an_unknown_app(respx_mock: respx.MockRouter, recorded: Recorded) -> None:
    respx_mock.get(f"{ITUNES_URL}/lookup").respond(json=recorded("lookup_missing.json"))

    result = runner.invoke(app, ["get", "1"])

    assert result.exit_code == 1
    assert "no app with id 1 in the US App Store" in result.output


def test_get_rejects_a_link_that_is_not_an_app() -> None:
    result = runner.invoke(app, ["get", "https://example.com/us/app/id1"])

    assert result.exit_code == 1
    assert "not an App Store app link or id" in result.output


def test_get_reports_network_errors(respx_mock: respx.MockRouter) -> None:
    respx_mock.get(f"{ITUNES_URL}/lookup").respond(404)

    result = runner.invoke(app, ["get", "1"])

    assert result.exit_code == 1
    assert "404" in result.output


def test_search_lucky_downloads_the_first_hit(
    respx_mock: respx.MockRouter, recorded: Recorded, google_art: str, tmp_path: Path
) -> None:
    respx_mock.get(f"{ITUNES_URL}/search", params={"country": "us"}).respond(
        json=recorded("search_google_us.json")
    )
    respx_mock.get(f"{google_art}/10000x10000bb.png").respond(content=encode_png((1024, 1024)))

    result = runner.invoke(app, ["search", "google", "-c", "us", "--lucky", "-o", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert "1. Google" in result.output
    assert (tmp_path / "Google_447.9_1024x1024.png").is_file()


def test_search_downloads_the_hit_you_pick(
    respx_mock: respx.MockRouter, recorded: Recorded, tmp_path: Path
) -> None:
    hits = recorded("search_google_us.json")
    respx_mock.get(f"{ITUNES_URL}/search", params={"term": "google chrome"}).respond(json=hits)
    respx_mock.get(f"{art_dir(hits['results'][1])}/10000x10000bb.png").respond(
        content=encode_png((1024, 1024))
    )

    result = runner.invoke(
        app, ["search", "google", "chrome", "-c", "us", "-o", str(tmp_path)], input="9\n2\n"
    )

    assert result.exit_code == 0, result.output
    assert (tmp_path / "Google Chrome_158.0.8127.35_1024x1024.png").is_file()


def test_search_covers_us_and_cn_by_default(
    respx_mock: respx.MockRouter, recorded: Recorded, google_art: str, tmp_path: Path
) -> None:
    us = respx_mock.get(f"{ITUNES_URL}/search", params={"country": "us"}).respond(
        json=recorded("search_google_us.json")
    )
    cn = respx_mock.get(f"{ITUNES_URL}/search", params={"country": "cn"}).respond(
        json=recorded("search_google_cn.json")
    )
    respx_mock.get(f"{google_art}/10000x10000bb.png").respond(content=encode_png((8, 8)))

    result = runner.invoke(app, ["search", "google", "--lucky", "-o", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert us.called
    assert cn.called
    assert "Google 地图" in result.output


def test_search_prompts_for_keywords_when_none_are_given(
    respx_mock: respx.MockRouter, recorded: Recorded, google_art: str, tmp_path: Path
) -> None:
    respx_mock.get(f"{ITUNES_URL}/search", params={"term": "google"}).respond(
        json=recorded("search_google_us.json")
    )
    respx_mock.get(f"{google_art}/10000x10000bb.png").respond(content=encode_png((8, 8)))

    result = runner.invoke(
        app, ["search", "-c", "us", "--lucky", "-o", str(tmp_path)], input="google\n"
    )

    assert result.exit_code == 0, result.output


def test_search_without_results(respx_mock: respx.MockRouter) -> None:
    respx_mock.get(f"{ITUNES_URL}/search").respond(json=NO_RESULTS)

    result = runner.invoke(app, ["search", "zzzz", "-c", "us"])

    assert result.exit_code == 0
    assert "No results" in result.output


def test_get_reports_file_system_errors(
    respx_mock: respx.MockRouter, recorded: Recorded, google_art: str, tmp_path: Path
) -> None:
    respx_mock.get(f"{ITUNES_URL}/lookup").respond(json=recorded("lookup_google_us.json"))
    respx_mock.get(f"{google_art}/10000x10000bb.png").respond(content=encode_png((8, 8)))
    not_a_folder = tmp_path / "file"
    not_a_folder.write_text("x")

    result = runner.invoke(app, ["get", "284815942", "-o", str(not_a_folder / "sub")])

    assert result.exit_code == 1
    assert "Error:" in result.output
    assert "Traceback" not in result.output


def test_get_dry_run_reports_a_missing_artwork_url(
    respx_mock: respx.MockRouter, recorded: Recorded
) -> None:
    lookup = recorded("lookup_google_us.json")
    for key in ("artworkUrl512", "artworkUrl100", "artworkUrl60"):
        del lookup["results"][0][key]
    respx_mock.get(f"{ITUNES_URL}/lookup").respond(json=lookup)

    result = runner.invoke(app, ["get", "284815942", "--dry-run"])

    assert result.exit_code == 1
    assert "unrecognised artwork URL" in result.output


def test_search_still_works_when_thumbnails_are_not_images(
    respx_mock: respx.MockRouter,
    recorded: Recorded,
    google_art: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(preview, "enabled", lambda env, stream: True)
    respx_mock.get(f"{ITUNES_URL}/search").respond(json=recorded("search_google_us.json"))
    respx_mock.get(url__regex=r"/64x64bb\.png$").respond(content=b"<html>proxy page</html>")
    respx_mock.get(f"{google_art}/10000x10000bb.png").respond(content=encode_png((8, 8)))

    result = runner.invoke(app, ["search", "google", "-c", "us", "-o", str(tmp_path)], input="1\n")

    assert result.exit_code == 0, result.output
    assert (tmp_path / "Google_447.9_8x8.png").is_file()
