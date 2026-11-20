"""Value types shared by the client, the service and the CLI."""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Self

_STORE_LINK = re.compile(
    r"(?:https?://)?(?:apps|itunes)\.apple\.com/"
    r"(?:(?P<country>[a-z]{2})/)?app/(?:[^/?#]+/)?id(?P<id>\d+)(?:[/?#].*)?",
    re.IGNORECASE,
)
_BARE_ID = re.compile(r"(?:id)?(?P<id>\d+)", re.IGNORECASE)
_ARTWORK_KEYS = ("artworkUrl512", "artworkUrl100", "artworkUrl60")


class InvalidAppRefError(ValueError):
    """The text is neither an App Store app link nor an app id."""


@dataclass(frozen=True, slots=True)
class AppRef:
    """An app id, plus the storefront country when the link names one."""

    track_id: int
    country: str | None = None

    @classmethod
    def parse(cls, text: str) -> Self:
        """Parse an App Store link (``apps.apple.com/us/app/name/id123``), ``id123`` or ``123``."""
        text = text.strip()
        if match := _STORE_LINK.fullmatch(text):
            country = match["country"]
            return cls(int(match["id"]), country.lower() if country else None)
        if match := _BARE_ID.fullmatch(text):
            return cls(int(match["id"]))
        raise InvalidAppRefError(f"not an App Store app link or id: {text!r}")


@dataclass(frozen=True, slots=True)
class AppInfo:
    """One app as the iTunes Lookup/Search API describes it in one storefront."""

    track_id: int
    name: str
    version: str
    bundle_id: str
    country: str
    artwork_url: str

    @property
    def store_url(self) -> str:
        return f"https://apps.apple.com/{self.country}/app/id{self.track_id}"

    @classmethod
    def from_itunes(cls, result: Mapping[str, Any], country: str) -> Self:
        """Build from one entry of an iTunes API ``results`` array."""
        artwork = next((result[key] for key in _ARTWORK_KEYS if result.get(key)), "")
        return cls(
            track_id=int(result["trackId"]),
            name=str(result["trackName"]).strip(),
            version=str(result.get("version", "")),
            bundle_id=str(result.get("bundleId", "")),
            country=country,
            artwork_url=str(artwork),
        )
