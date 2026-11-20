"""Command-line interface: ``appicon get`` and ``appicon search``."""

import asyncio
import os
import sys
from collections.abc import Awaitable, Callable
from enum import StrEnum
from pathlib import Path
from typing import Annotated, NoReturn

import httpx
import typer

from appicon import __version__, preview
from appicon.artwork import LARGEST, icon_url
from appicon.clients import AppNotFoundError, ItunesClient, make_http_client
from appicon.models import AppInfo
from appicon.service import IconService

DEFAULT_COUNTRIES = ["us", "cn"]
THUMBNAIL_SIZE = 64
PREVIEW_WIDTH = 128
DOWNLOADS = Path.home() / "Downloads"


class Format(StrEnum):
    png = "png"
    jpg = "jpg"


Output = Annotated[
    Path, typer.Option("--output", "-o", file_okay=False, help="Folder to save the icon in.")
]
Size = Annotated[
    int,
    typer.Option(
        "--size", "-s", min=1, help="Edge length in pixels. The default gets the original."
    ),
]
ImageFormat = Annotated[Format, typer.Option("--format", "-f", help="Image format.")]
Proxy = Annotated[
    str | None,
    typer.Option(
        help="Proxy URL such as socks5://127.0.0.1:1080. Default: HTTPS_PROXY / ALL_PROXY.",
        show_default=False,
    ),
]

app = typer.Typer(no_args_is_help=True, help="Download App Store app icons at full resolution.")


def _show_version(value: bool) -> None:
    if value:
        typer.echo(f"appicon {__version__}")
        raise typer.Exit


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version", callback=_show_version, is_eager=True, help="Show the version and exit."
        ),
    ] = False,
) -> None:
    """Download App Store app icons at full resolution."""


def _fail(message: str) -> NoReturn:
    typer.secho(f"Error: {message}", err=True, fg=typer.colors.RED)
    raise typer.Exit(1)


def _run[T](proxy: str | None, job: Callable[[IconService], Awaitable[T]]) -> T:
    """Run one async job with a fresh HTTP client, turning expected errors into messages."""

    async def go() -> T:
        async with make_http_client(proxy) as http:
            return await job(IconService(ItunesClient(http)))

    try:
        return asyncio.run(go())
    except httpx.HTTPError as exc:
        _fail(f"network error: {exc}")
    except (AppNotFoundError, ValueError, OSError) as exc:
        _fail(str(exc))


def _describe(app_info: AppInfo) -> None:
    typer.secho(f"{app_info.name} {app_info.version}".rstrip(), bold=True)
    typer.echo(f"  Bundle ID  {app_info.bundle_id}")
    typer.echo(f"  Store      {app_info.store_url}")


def _pick(count: int) -> int:
    """Ask for a result number until it is between 1 and ``count``."""
    while True:
        choice = int(typer.prompt("Select", type=int))
        if 1 <= choice <= count:
            return choice
        typer.echo(f"Pick a number from 1 to {count}.")


def _show_saved(path: Path) -> None:
    typer.echo(f"Saved {path}")
    if preview.enabled(os.environ, sys.stdout):
        typer.echo(preview.inline_image(path.read_bytes(), name=path.name, width=PREVIEW_WIDTH))


@app.command()
def get(
    ref: Annotated[
        str | None,
        typer.Argument(
            metavar="URL_OR_ID", help="App Store link, id123 or 123.", show_default=False
        ),
    ] = None,
    country: Annotated[
        str | None,
        typer.Option(
            "--country",
            "-c",
            help="Storefront such as us or cn. Default: the one in the link, else us.",
            show_default=False,
        ),
    ] = None,
    size: Size = LARGEST,
    fmt: ImageFormat = Format.png,
    output: Output = DOWNLOADS,
    name: Annotated[
        str | None,
        typer.Option(help="Use this instead of the app name in the file name.", show_default=False),
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show the app and icon URL without downloading.")
    ] = False,
    proxy: Proxy = None,
) -> None:
    """Download the icon of one app."""
    app_ref: str = ref or typer.prompt("App Store link or id")
    found = _run(proxy, lambda service: service.resolve(app_ref, country))
    _describe(found)
    if dry_run:
        try:
            url = icon_url(found.artwork_url, size, fmt.value)
        except ValueError as exc:
            _fail(str(exc))
        typer.echo(f"  Icon       {url}")
        return
    path = _run(
        proxy, lambda service: service.download(found, output, size=size, fmt=fmt.value, name=name)
    )
    _show_saved(path)


@app.command()
def search(
    keywords: Annotated[
        list[str] | None,
        typer.Argument(metavar="KEYWORDS...", help="Words to search for.", show_default=False),
    ] = None,
    country: Annotated[
        list[str] | None,
        typer.Option(
            "--country",
            "-c",
            help="Storefront to search; repeat for several. Default: us and cn.",
            show_default=False,
        ),
    ] = None,
    limit: Annotated[int, typer.Option(min=1, max=200, help="Results per storefront.")] = 10,
    lucky: Annotated[
        bool, typer.Option("--lucky", help="Download the first result without asking.")
    ] = False,
    size: Size = LARGEST,
    fmt: ImageFormat = Format.png,
    output: Output = DOWNLOADS,
    proxy: Proxy = None,
) -> None:
    """Search the App Store and download the icon you pick."""
    term = " ".join(keywords) if keywords else str(typer.prompt("Search for"))
    countries = country or DEFAULT_COUNTRIES
    show_thumbnails = preview.enabled(os.environ, sys.stdout) and not lucky

    async def find(service: IconService) -> tuple[list[AppInfo], bytes | None]:
        apps = await service.search(term, countries, limit)
        if not (show_thumbnails and apps):
            return apps, None
        try:
            thumbnails = await asyncio.gather(
                *(service.fetch_icon(app, THUMBNAIL_SIZE) for app in apps)
            )
            return apps, preview.side_by_side(thumbnails)
        except (httpx.HTTPError, ValueError, OSError):
            return apps, None  # previews are a nicety; the list still works without them

    apps, strip = _run(proxy, find)
    if not apps:
        typer.echo("No results.")
        return
    for number, hit in enumerate(apps, start=1):
        typer.echo(f"{number:>2}. {hit.name}  [{hit.country}]  {hit.store_url}")
    if strip:
        typer.echo(preview.inline_image(strip))

    choice = 1 if lucky else _pick(len(apps))
    chosen = apps[choice - 1]
    path = _run(proxy, lambda service: service.download(chosen, output, size=size, fmt=fmt.value))
    _show_saved(path)
