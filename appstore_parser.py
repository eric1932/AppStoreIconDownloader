import http.client
import urllib.error
from urllib import request

from AppMetadata import AppMetadata
from src.utils.url_util import clean_store_url


# TODO example: https://apps.apple.com/cn/app/id1540095522
def _parse_appstore_html(print_log, web_html, store_url):
    app_metadata = AppMetadata(store_url, html_page=web_html)
    metadata = app_metadata.get_metadata()
    return (metadata.get('app_name'),
            metadata.get('app_version'),
            metadata.get('original_type'),
            app_metadata.get_url())


def get_orig_img_url(store_url: str, print_log: bool = True):
    store_url, _ = clean_store_url(store_url)
    # try reg match
    try:
        response: http.client.HTTPResponse
        with request.urlopen(store_url) as response:
            web_html = response.read().decode()
    except urllib.error.HTTPError as e:
        # response.status might be 404
        raise ValueError("AppStore:") from e

    app_name, app_version, img_ext, img_url_orig = _parse_appstore_html(print_log, web_html, store_url)

    return app_name, store_url, app_version, img_ext, img_url_orig


# TODO merge sync & async
async def async_get_orig_img_url(store_url: str, print_log: bool = True):
    store_url, _ = clean_store_url(store_url)
    try:
        app_metadata = AppMetadata(store_url)
        await app_metadata.await_html_task()
    except Exception as e:
        print(e)  # TODO
        raise ValueError("AppStore:") from e

    metadata = app_metadata.get_metadata()
    return (metadata.get('app_name'),
            metadata.get('store_url'),
            metadata.get('app_version'),
            metadata.get('original_type'),
            app_metadata.get_url())
