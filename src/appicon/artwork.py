"""Pure helpers for icon URLs, file names and image bytes. No network or disk access."""

import re
from io import BytesIO

from PIL import Image, UnidentifiedImageError

from appicon.models import AppInfo

LARGEST = 10000
"""Asking the CDN for more pixels than the original has returns the original."""

FORMATS = ("png", "jpg")

_SIZE_SUFFIX = re.compile(r"/\d+x\d+[a-z]*\.[a-z]+$")
_UNSAFE_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f\x7f]')


def icon_url(artwork_url: str, size: int = LARGEST, fmt: str = "png") -> str:
    """Rewrite an iTunes artwork URL (``.../512x512bb.jpg``) to another size and format."""
    if fmt not in FORMATS:
        raise ValueError(f"unsupported format {fmt!r}; choose from {', '.join(FORMATS)}")
    if size <= 0:
        raise ValueError(f"size must be positive, got {size}")
    url, count = _SIZE_SUFFIX.subn(f"/{size}x{size}bb.{fmt}", artwork_url)
    if count != 1:
        raise ValueError(f"unrecognised artwork URL: {artwork_url!r}")
    return url


def safe_filename(text: str) -> str:
    """Replace characters that are unsafe in file names; never returns an empty string."""
    cleaned = _UNSAFE_CHARS.sub("_", text.strip()).strip(". ")
    return cleaned or "app"


def icon_filename(app: AppInfo, size: tuple[int, int], fmt: str, name: str | None = None) -> str:
    """``<name>_<version>_<width>x<height>.<fmt>``, e.g. ``Google_447.9_1024x1024.png``."""
    parts = [name or app.name]
    if app.version:
        parts.append(app.version)
    parts.append(f"{size[0]}x{size[1]}")
    return f"{safe_filename('_'.join(parts))}.{fmt}"


def image_size(data: bytes) -> tuple[int, int]:
    """Width and height of an encoded image."""
    try:
        with Image.open(BytesIO(data)) as image:
            return image.size
    except UnidentifiedImageError as exc:
        raise ValueError("not an image") from exc
