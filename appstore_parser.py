import html
import http.client
import re
import urllib.error
from urllib import request

from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector

from Exceptions import NoIconMatchException
from proxy import ALL_PROXY
from utils.url_util import clean_store_url


# TODO parse html as tree
# TODO example: https://apps.apple.com/cn/app/id1540095522
def _parse_appstore_html(print_log, store_region, web_html):
    # alternative re match "https:\/\/is.*?-ssl\.mzstatic\.com\/image\/thumb\/.*?AppIcon.*?\.png\/230x0w\.png"
    # image_match = re.findall(r"https:\/\/is.*?-ssl\.mzstatic\.com\/image\/thumb\/.*?\.png\/230x0w\.png", web_html)
    # use png first because its quality is the best
    img_ext = 'png'
    image_match = re.search(
        r"https://is.*?-ssl\.mzstatic\.com/image/thumb/.*?\.png/230x(0w|[0-9]+sr)\.png",
        web_html)
    if (not image_match
            or ("appicon" not in image_match.group().lower()
                and "logo" not in image_match.group().lower())):  # TODO temp fix
        img_ext = 'webp'
        image_match = re.search(
            r"https://is.*?-ssl\.mzstatic\.com/image/thumb/.*?\.webp/230x(0w|[0-9]+sr)\.webp",
            web_html)
        if (not image_match
                or ("appicon" not in image_match.group().lower()
                    and "logo" not in image_match.group().lower())):  # TODO temp fix
            img_ext = 'jpg'
            image_match = re.search(
                r"https://is.*?-ssl\.mzstatic\.com/image/thumb/.*?\.(jpg|jpeg)/230x(0w|[0-9]+sr)\.(jpg|jpeg)",
                web_html)
            if not image_match:
                raise NoIconMatchException('no icon matches found!')
    if print_log:
        print("found image url!")
    img_url_orig = image_match.group()
    if print_log:
        print(img_url_orig)
    flag_imessage = "iMessage" in img_url_orig
    # Get app name
    # alternative way
    # <h1 class="product-header__title app-header__title">
    #           王者荣耀-表情包
    #             <span class="badge badge--product-title">4+</span>
    #         </h1>
    if store_region == 'cn':
        app_name = re.search("<title>‎App\xa0Store 上的“(.*)”</title>", web_html).group(1)
    else:
        app_name = re.search(r"<title>[\s|\u200e]*(.*) on the App[\xa0|\s]+Store\s*</title>", web_html).group(1)
    # unescape html encoding
    app_name = html.unescape(app_name)
    if not flag_imessage:
        # Get app version
        # '<p class="l-column small-6 medium-12 whats-new__latest__version">Version 105.0</p>'
        try:
            if store_region == 'cn':
                app_version = re.search(r"whats-new__latest__version\"\s?(data-test-version-number)?>版本 (.*?)</p>",
                                        web_html).group(2)
            else:
                app_version = re.search(r"whats-new__latest__version\"\s?(data-test-version-number)?>Version (.*?)</p>",
                                        web_html).group(2)
        except AttributeError:
            # TODO
            app_version = ""
    else:
        # TODO
        app_version = ""
    return app_name, app_version, img_ext, img_url_orig


def get_orig_img_url(store_url: str, print_log: bool = True):
    app_url_cleaned, store_region = clean_store_url(store_url)
    # try reg match
    try:
        response: http.client.HTTPResponse
        with request.urlopen(app_url_cleaned) as response:
            web_html = response.read().decode()
    except urllib.error.HTTPError as e:
        # response.status might be 404
        raise ValueError("AppStore:") from e

    app_name, app_version, img_ext, img_url_orig = _parse_appstore_html(print_log, store_region, web_html)

    return app_name, app_url_cleaned, app_version, img_ext, img_url_orig


async def async_get_orig_img_url(store_url: str, print_log: bool = True):
    app_url_cleaned, store_region = clean_store_url(store_url)
    # try reg match
    try:
        async with ClientSession(connector=ProxyConnector.from_url(ALL_PROXY)) if ALL_PROXY \
                else ClientSession() as session:
            async with session.get(app_url_cleaned) as response:
                response = await response.read()
                response = response.decode()
                web_html = response
    except Exception as e:
        print(e)  # TODO
        raise ValueError("AppStore:") from e

    try:
        app_name, app_version, img_ext, img_url_orig = _parse_appstore_html(print_log, store_region, web_html)
    except NoIconMatchException:
        # print(f"store_url: {store_url}")
        return '', '', '', '', ''

    return app_name, app_url_cleaned, app_version, img_ext, img_url_orig
