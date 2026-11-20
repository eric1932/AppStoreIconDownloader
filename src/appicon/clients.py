"""HTTP access to the iTunes Search/Lookup API and the artwork CDN."""

import asyncio
from typing import Any

import httpx

from appicon import __version__
from appicon.models import AppInfo

ITUNES_URL = "https://itunes.apple.com"

_TRANSIENT_STATUS = frozenset({429, 500, 502, 503, 504})


class AppNotFoundError(LookupError):
    """The Lookup API has no app with this id in this storefront."""

    def __init__(self, track_id: int, country: str) -> None:
        super().__init__(f"no app with id {track_id} in the {country.upper()} App Store")
        self.track_id = track_id
        self.country = country


def make_http_client(proxy: str | None = None, timeout: float = 15.0) -> httpx.AsyncClient:
    """An HTTP client for :class:`ItunesClient`.

    Without ``proxy``, the usual environment variables (``HTTPS_PROXY``, ``ALL_PROXY``,
    including ``socks5://`` URLs) are honoured.
    """
    return httpx.AsyncClient(
        proxy=proxy,
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": f"appicon/{__version__}"},
    )


class ItunesClient:
    """Thin async wrapper over the iTunes Lookup/Search endpoints, with retries."""

    def __init__(self, http: httpx.AsyncClient, *, attempts: int = 3, backoff: float = 0.5) -> None:
        self._http = http
        self._attempts = attempts
        self._backoff = backoff

    async def lookup(self, track_id: int, country: str) -> AppInfo:
        data = await self._get_json("/lookup", {"id": str(track_id), "country": country})
        results = data.get("results") or []
        if not results:
            raise AppNotFoundError(track_id, country)
        return AppInfo.from_itunes(results[0], country)

    async def search(self, term: str, country: str, limit: int = 10) -> list[AppInfo]:
        params = {"term": term, "entity": "software", "country": country, "limit": str(limit)}
        data = await self._get_json("/search", params)
        return [AppInfo.from_itunes(result, country) for result in data.get("results", [])]

    async def fetch(self, url: str) -> bytes:
        response = await self._get(url)
        return response.content

    async def _get_json(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        response = await self._get(f"{ITUNES_URL}{path}", params)
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError(f"unexpected iTunes API response from {path}")
        return data

    async def _get(self, url: str, params: dict[str, str] | None = None) -> httpx.Response:
        """GET with retries on connection errors, 429 and 5xx; other errors raise at once."""
        for attempt in range(1, self._attempts + 1):
            last = attempt == self._attempts
            try:
                response = await self._http.get(url, params=params)
            except httpx.TransportError:
                if last:
                    raise
            else:
                if last or response.status_code not in _TRANSIENT_STATUS:
                    return response.raise_for_status()
            await asyncio.sleep(self._backoff * attempt)
        raise AssertionError("unreachable")  # pragma: no cover
