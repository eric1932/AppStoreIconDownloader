"""Use cases: resolve an app, search the store, download its icon."""

import asyncio
from collections.abc import Iterable
from pathlib import Path

from appicon.artwork import LARGEST, icon_filename, icon_url, image_size
from appicon.clients import ItunesClient
from appicon.models import AppInfo, AppRef


class IconService:
    """Everything the CLI needs, written once and async."""

    def __init__(self, client: ItunesClient, *, default_country: str = "us") -> None:
        self._client = client
        self._default_country = default_country

    async def resolve(self, ref: str | AppRef, country: str | None = None) -> AppInfo:
        """Look up an app from a link or id.

        The storefront is ``country`` if given, else the one in the link, else the default.
        """
        if isinstance(ref, str):
            ref = AppRef.parse(ref)
        return await self._client.lookup(
            ref.track_id, country or ref.country or self._default_country
        )

    async def search(self, term: str, countries: Iterable[str], limit: int = 10) -> list[AppInfo]:
        """Search several storefronts at once; the first storefront to list an app wins."""
        per_country = await asyncio.gather(
            *(self._client.search(term, country, limit) for country in countries)
        )
        seen: set[int] = set()
        merged: list[AppInfo] = []
        for apps in per_country:
            for app in apps:
                if app.track_id not in seen:
                    seen.add(app.track_id)
                    merged.append(app)
        return merged

    async def fetch_icon(self, app: AppInfo, size: int = LARGEST, fmt: str = "png") -> bytes:
        return await self._client.fetch(icon_url(app.artwork_url, size, fmt))

    async def download(
        self,
        app: AppInfo,
        out_dir: Path,
        *,
        size: int = LARGEST,
        fmt: str = "png",
        name: str | None = None,
    ) -> Path:
        """Save the icon as ``<name>_<version>_<w>x<h>.<fmt>`` in ``out_dir`` and return its path.

        The default size asks for more pixels than any original has, so the CDN sends the original.
        """
        data = await self.fetch_icon(app, size, fmt)
        path = out_dir / icon_filename(app, image_size(data), fmt, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path
