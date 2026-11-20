from io import BytesIO

import pytest
from PIL import Image

from appicon.preview import enabled, inline_image, side_by_side, supported


def encode(size: tuple[int, int]) -> bytes:
    buffer = BytesIO()
    Image.new("RGBA", size, (255, 0, 0, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({"TERM_PROGRAM": "iTerm.app"}, True),
        ({"LC_TERMINAL": "iTerm2"}, True),  # over ssh
        ({"LC_TERMINAL": "iTerm2", "TERM_PROGRAM": "tmux", "TMUX": "/tmp/tmux-1/default"}, False),
        ({"TERM_PROGRAM": "Apple_Terminal"}, False),
        ({}, False),
    ],
)
def test_supported_only_in_iterm(env: dict[str, str], expected: bool) -> None:
    assert supported(env) is expected


def test_inline_image_is_an_iterm_file_escape() -> None:
    # base64("G") == "Rw==", base64(b"abc") == "YWJj"
    assert inline_image(b"abc", name="G", width=64) == (
        "\x1b]1337;File=name=Rw==;size=3;width=64px;inline=1:YWJj\x07"
    )


def test_inline_image_without_name_or_width() -> None:
    assert inline_image(b"abc") == "\x1b]1337;File=size=3;inline=1:YWJj\x07"


def test_side_by_side_puts_images_in_one_row_with_gaps() -> None:
    row = side_by_side([encode((4, 2)), encode((2, 3)), encode((1, 1))], gap=8)

    with Image.open(BytesIO(row)) as image:
        assert image.format == "PNG"
        assert image.size == (4 + 8 + 2 + 8 + 1, 3)
        assert image.getpixel((5, 0)) == (0, 0, 0, 0)  # the gap is transparent
        assert image.getpixel((12, 0)) == (255, 0, 0, 255)  # second image starts at 4 + 8


class FakeStream:
    def __init__(self, tty: bool) -> None:
        self.tty = tty

    def isatty(self) -> bool:
        return self.tty


@pytest.mark.parametrize(
    ("env", "tty", "expected"),
    [
        ({"TERM_PROGRAM": "iTerm.app"}, True, True),
        ({"TERM_PROGRAM": "iTerm.app"}, False, False),  # piped or redirected
        ({}, True, False),
    ],
)
def test_enabled_needs_iterm_and_a_terminal(env: dict[str, str], tty: bool, expected: bool) -> None:
    assert enabled(env, FakeStream(tty)) is expected
