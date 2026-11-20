from io import BytesIO

import pytest
from PIL import Image

from appicon.artwork import icon_filename, icon_url, image_size, safe_filename
from appicon.models import AppInfo

ART_DIR = "https://is1-ssl.mzstatic.com/image/thumb/Purple211/v4/72/33/d8/x/SuperG.png"
GOOGLE = AppInfo(
    track_id=284815942,
    name="Google",
    version="447.9",
    bundle_id="com.google.GoogleMobile",
    country="us",
    artwork_url=f"{ART_DIR}/512x512bb.jpg",
)


def encode(size: tuple[int, int], fmt: str) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size).save(buffer, format=fmt)
    return buffer.getvalue()


def test_icon_url_rewrites_size_and_format() -> None:
    assert icon_url(GOOGLE.artwork_url, 1024, "png") == f"{ART_DIR}/1024x1024bb.png"


def test_icon_url_defaults_to_a_png_larger_than_any_original() -> None:
    assert icon_url(GOOGLE.artwork_url) == f"{ART_DIR}/10000x10000bb.png"


@pytest.mark.parametrize(
    ("url", "size", "fmt"),
    [
        (GOOGLE.artwork_url, 64, "gif"),
        (GOOGLE.artwork_url, 0, "png"),
        ("https://example.com/icon.png", 64, "png"),
        ("", 64, "png"),
    ],
)
def test_icon_url_rejects_bad_input(url: str, size: int, fmt: str) -> None:
    with pytest.raises(ValueError):  # noqa: PT011 - every case is a plain ValueError
        icon_url(url, size, fmt)


@pytest.mark.parametrize(
    ("raw", "safe"),
    [
        ("Google", "Google"),
        ("Notes / Docs", "Notes _ Docs"),
        ('a:b*c?"d<e>f|g\\h', "a_b_c__d_e_f_g_h"),
        ("bad\x00name\n", "bad_name"),
        ("  .hidden. ", "hidden"),
        ("微信", "微信"),
        ("///", "___"),
        ("", "app"),
    ],
)
def test_safe_filename(raw: str, safe: str) -> None:
    assert safe_filename(raw) == safe


def test_icon_filename_has_name_version_and_pixel_size() -> None:
    assert icon_filename(GOOGLE, (1024, 1024), "png") == "Google_447.9_1024x1024.png"


def test_icon_filename_uses_override_name_safely() -> None:
    assert icon_filename(GOOGLE, (64, 64), "jpg", name="My/Icon") == "My_Icon_447.9_64x64.jpg"


def test_icon_filename_skips_missing_version() -> None:
    app = AppInfo(1, "Tiny", "", "com.example.tiny", "us", GOOGLE.artwork_url)

    assert icon_filename(app, (512, 512), "png") == "Tiny_512x512.png"


@pytest.mark.parametrize("fmt", ["PNG", "JPEG"])
def test_image_size_reads_encoded_images(fmt: str) -> None:
    assert image_size(encode((5, 3), fmt)) == (5, 3)


def test_image_size_rejects_non_images() -> None:
    with pytest.raises(ValueError, match="not an image"):
        image_size(b"<html>Bad Request</html>")
