"""Inline image previews for iTerm2 (its OSC 1337 file protocol). Other terminals get nothing."""

import base64
from collections.abc import Mapping, Sequence
from io import BytesIO
from typing import Protocol

from PIL import Image


class _Stream(Protocol):
    def isatty(self) -> bool: ...


def supported(env: Mapping[str, str]) -> bool:
    """True inside iTerm2, also over ssh where ``LC_TERMINAL`` is forwarded.

    tmux swallows the escape sequence, so it counts as unsupported.
    """
    if "TMUX" in env or env.get("TERM_PROGRAM") == "tmux":
        return False
    return env.get("TERM_PROGRAM") == "iTerm.app" or env.get("LC_TERMINAL") == "iTerm2"


def enabled(env: Mapping[str, str], stream: _Stream) -> bool:
    """Show previews only in iTerm2 and only when ``stream`` is the terminal, not a pipe or file."""
    return supported(env) and stream.isatty()


def inline_image(data: bytes, name: str = "", width: int | None = None) -> str:
    """The escape sequence that makes iTerm2 draw ``data`` inline, ``width`` in pixels."""
    args = []
    if name:
        args.append(f"name={base64.b64encode(name.encode()).decode('ascii')}")
    args.append(f"size={len(data)}")
    if width:
        args.append(f"width={width}px")
    args.append("inline=1")
    return f"\x1b]1337;File={';'.join(args)}:{base64.b64encode(data).decode('ascii')}\x07"


def side_by_side(images: Sequence[bytes], gap: int = 8) -> bytes:
    """One PNG with ``images`` left to right, ``gap`` transparent pixels apart."""
    decoded = [Image.open(BytesIO(data)).convert("RGBA") for data in images]
    width = sum(image.width for image in decoded) + gap * (len(decoded) - 1)
    height = max(image.height for image in decoded)
    row = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    x = 0
    for image in decoded:
        row.paste(image, (x, 0))
        x += image.width + gap
    buffer = BytesIO()
    row.save(buffer, format="PNG")
    return buffer.getvalue()
