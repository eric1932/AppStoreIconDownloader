import html
import re
import urllib.error
from sys import exit
from urllib import request as request

from aiohttp import ClientSession


def _get_clean_store_url(app_url):
    # match App Store URLs
    match = re.search(r"(apps\.apple\.com/([a-z]{2})/app/)(.*/)?(id[0-9]+)", app_url)
    # groups() example output: ('apps.apple.com/us/app/', 'us', 'google/', 'id284815942')
    if not match:
        raise ValueError("invalid App Store URL!")
    # enforce https
    app_url_cleaned = r'https://' + match.group(1) + match.group(4)
    store_region = match.group(2)
    return app_url_cleaned, store_region


def _parse_appstore_html(print_log, store_region, web_html):
    # alternative re match "https:\/\/is.*?-ssl\.mzstatic\.com\/image\/thumb\/.*?AppIcon.*?\.png\/230x0w\.png"
    # image_match = re.findall(r"https:\/\/is.*?-ssl\.mzstatic\.com\/image\/thumb\/.*?\.png\/230x0w\.png", web_html)
    image_match = re.search(r"https://is.*?-ssl\.mzstatic\.com/image/thumb/.*?\.(png|jpg|jpeg)/230x0w\.("
                            r"png|jpg|jpeg)", web_html)
    if not image_match:
        if print_log:
            print('no matches found!')
        exit(1)
    if print_log:
        print("found image url!")
    img_ext = image_match.group(2)
    # Get app name
    if store_region == 'cn':
        app_name = re.search("<title>‎App\xa0Store 上的“(.*)”</title>", web_html).group(1)
    else:
        app_name = re.search("<title>\u200e(.*) on the App\xa0Store</title>", web_html).group(1)
    # unescape html encoding
    app_name = html.unescape(app_name)
    # Get app version
    # '<p class="l-column small-6 medium-12 whats-new__latest__version">Version 105.0</p>'
    if store_region == 'cn':
        app_version = re.search(r"whats-new__latest__version\"\s?(data-test-version-number)?>版本 (.*?)</p>",
                                web_html).group(2)
    else:
        app_version = re.search(r"whats-new__latest__version\"\s?(data-test-version-number)?>Version (.*?)</p>",
                                web_html).group(2)
    img_url_orig = image_match.group()
    return app_name, app_version, img_ext, img_url_orig


def get_orig_img_url(store_url: str, print_log: bool = True):
    app_url_cleaned, store_region = _get_clean_store_url(store_url)
    # try reg match
    try:
        with request.urlopen(app_url_cleaned) as response:
            web_html = response.read().decode()
    except urllib.error.HTTPError:
        raise ValueError("AppStore:")

    app_name, app_version, img_ext, img_url_orig = _parse_appstore_html(print_log, store_region, web_html)

    return app_name, app_url_cleaned, app_version, img_ext, img_url_orig


async def async_get_orig_img_url(store_url: str, print_log: bool = True):
    app_url_cleaned, store_region = _get_clean_store_url(store_url)
    # try reg match
    try:
        async with ClientSession() as session:
            async with session.get(app_url_cleaned) as response:
                response = await response.read()
                response = response.decode()
                web_html = response
    except Exception as e:
        print(e)  # TODO
        raise ValueError("AppStore:")

    app_name, app_version, img_ext, img_url_orig = _parse_appstore_html(print_log, store_region, web_html)

    return app_name, app_url_cleaned, app_version, img_ext, img_url_orig


def change_img_url_size(image_url_Xx0w, img_size: int):
    return re.sub(r"[0-9]+x0w", f'{img_size}x0w', image_url_Xx0w)
