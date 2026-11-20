from collections.abc import Callable
from typing import Any

import pytest

from appicon.models import AppInfo, AppRef, InvalidAppRefError

type Recorded = Callable[[str], Any]
GOOGLE_ARTWORK_512 = (
    "https://is1-ssl.mzstatic.com/image/thumb/Purple211/v4/72/33/d8/"
    "7233d884-35b3-1ed3-4376-b3888064295f/"
    "SuperG_ios26-0-0-1x_U007epad-0-0-0-1-0-0-sRGB-0-0-0-85-220.png/512x512bb.jpg"
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("284815942", AppRef(284815942)),
        ("id284815942", AppRef(284815942)),
        ("https://apps.apple.com/us/app/google/id284815942", AppRef(284815942, "us")),
        ("https://apps.apple.com/us/app/google/id284815942?uo=4", AppRef(284815942, "us")),
        ("apps.apple.com/cn/app/id414478124", AppRef(414478124, "cn")),
        ("https://apps.apple.com/cn/app/%E5%BE%AE%E4%BF%A1/id414478124", AppRef(414478124, "cn")),
        ("https://apps.apple.com/app/id284815942", AppRef(284815942)),
        ("https://itunes.apple.com/GB/app/whatsapp/id310633997?mt=8", AppRef(310633997, "gb")),
        ("  https://apps.apple.com/us/app/google/id284815942\n", AppRef(284815942, "us")),
    ],
)
def test_parse_accepts_app_links_and_ids(text: str, expected: AppRef) -> None:
    assert AppRef.parse(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "",
        "google",
        "id",
        "https://play.google.com/store/apps/details?id=123",
        "https://apps.apple.com/us/developer/google/id281956209",
        "https://example.com/us/app/google/id284815942",
    ],
)
def test_parse_rejects_anything_else(text: str) -> None:
    with pytest.raises(InvalidAppRefError):
        AppRef.parse(text)


def test_from_itunes_maps_a_lookup_result(recorded: Recorded) -> None:
    data = recorded("lookup_google_us.json")

    app = AppInfo.from_itunes(data["results"][0], country="us")

    assert app == AppInfo(
        track_id=284815942,
        name="Google",
        version="447.9",
        bundle_id="com.google.GoogleMobile",
        country="us",
        artwork_url=GOOGLE_ARTWORK_512,
    )
    assert app.store_url == "https://apps.apple.com/us/app/id284815942"


def test_from_itunes_falls_back_to_smaller_artwork() -> None:
    result = {
        "trackId": 1,
        "trackName": "Tiny",
        "version": "1.0",
        "bundleId": "com.example.tiny",
        "artworkUrl100": "https://is1-ssl.mzstatic.com/image/thumb/x/icon.png/100x100bb.jpg",
    }

    app = AppInfo.from_itunes(result, country="jp")

    assert app.artwork_url == "https://is1-ssl.mzstatic.com/image/thumb/x/icon.png/100x100bb.jpg"
