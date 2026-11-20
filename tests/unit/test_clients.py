from collections.abc import AsyncIterator, Callable
from typing import Any

import httpx
import pytest
import respx

from appicon.clients import ITUNES_URL, AppNotFoundError, InvalidCountryError, ItunesClient

pytestmark = pytest.mark.anyio
type Recorded = Callable[[str], Any]
ICON = "https://is1-ssl.mzstatic.com/image/thumb/x/icon.png/64x64bb.png"


@pytest.fixture
async def client() -> AsyncIterator[ItunesClient]:
    async with httpx.AsyncClient() as http:
        yield ItunesClient(http, backoff=0)


async def test_lookup_returns_the_app_in_the_requested_storefront(
    client: ItunesClient, respx_mock: respx.MockRouter, recorded: Recorded
) -> None:
    respx_mock.get(f"{ITUNES_URL}/lookup", params={"id": "284815942", "country": "us"}).respond(
        json=recorded("lookup_google_us.json")
    )

    app = await client.lookup(284815942, "us")

    assert (app.track_id, app.name, app.country) == (284815942, "Google", "us")


async def test_lookup_of_unknown_id_raises_not_found(
    client: ItunesClient, respx_mock: respx.MockRouter, recorded: Recorded
) -> None:
    respx_mock.get(f"{ITUNES_URL}/lookup").respond(json=recorded("lookup_missing.json"))

    with pytest.raises(AppNotFoundError, match="no app with id 1 in the US App Store"):
        await client.lookup(1, "us")


async def test_search_asks_for_software_and_keeps_api_order(
    client: ItunesClient, respx_mock: respx.MockRouter, recorded: Recorded
) -> None:
    respx_mock.get(
        f"{ITUNES_URL}/search",
        params={"term": "google", "entity": "software", "country": "us", "limit": "3"},
    ).respond(json=recorded("search_google_us.json"))

    apps = await client.search("google", "us", limit=3)

    assert [app.track_id for app in apps] == [284815942, 535886823, 422689480]
    assert {app.country for app in apps} == {"us"}


async def test_transient_failures_are_retried(
    client: ItunesClient, respx_mock: respx.MockRouter, recorded: Recorded
) -> None:
    route = respx_mock.get(f"{ITUNES_URL}/lookup").mock(
        side_effect=[
            httpx.ConnectError("boom"),
            httpx.Response(503),
            httpx.Response(200, json=recorded("lookup_google_us.json")),
        ]
    )

    app = await client.lookup(284815942, "us")

    assert app.name == "Google"
    assert route.call_count == 3


async def test_gives_up_after_three_attempts(
    client: ItunesClient, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.get(f"{ITUNES_URL}/lookup").respond(503)

    with pytest.raises(httpx.HTTPStatusError):
        await client.lookup(284815942, "us")
    assert route.call_count == 3


async def test_client_errors_are_not_retried(
    client: ItunesClient, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.get(ICON).respond(400, json={"error": "bad size"})

    with pytest.raises(httpx.HTTPStatusError):
        await client.fetch(ICON)
    assert route.call_count == 1


async def test_fetch_returns_the_response_body(
    client: ItunesClient, respx_mock: respx.MockRouter
) -> None:
    respx_mock.get(ICON).respond(content=b"\x89PNG fake bytes")

    assert await client.fetch(ICON) == b"\x89PNG fake bytes"


async def test_lookup_of_a_developer_id_raises_not_found(
    client: ItunesClient, respx_mock: respx.MockRouter, recorded: Recorded
) -> None:
    respx_mock.get(f"{ITUNES_URL}/lookup").respond(json=recorded("lookup_developer.json"))

    with pytest.raises(AppNotFoundError, match="no app with id 281956209"):
        await client.lookup(281956209, "us")


async def test_lookup_names_a_rejected_country_code(
    client: ItunesClient, respx_mock: respx.MockRouter
) -> None:
    respx_mock.get(f"{ITUNES_URL}/lookup").respond(400)

    with pytest.raises(InvalidCountryError, match="'uk'"):
        await client.lookup(284815942, "uk")


async def test_search_names_a_rejected_country_code(
    client: ItunesClient, respx_mock: respx.MockRouter
) -> None:
    respx_mock.get(f"{ITUNES_URL}/search").respond(400)

    with pytest.raises(InvalidCountryError, match="'uk'"):
        await client.search("google", "uk")
