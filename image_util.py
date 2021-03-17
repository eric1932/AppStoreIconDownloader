import asyncio
import base64
import html
import re
import urllib.error
from io import BytesIO
from sys import exit
from typing import Union, List, Tuple
from urllib import request as request

from PIL import Image
from aiohttp import ClientSession


def show_image_in_terminal(image_name: str, image_binary: bytes, image_side_len: Union[int, tuple]):
    b64_name = base64.b64encode(image_name.encode('utf-8')).decode('utf-8')  # in case of non-ascii chars
    b64_img = base64.b64encode(image_binary).decode('ascii')  # decode to remove the b'___' wrapping
    print(f"\n"
          f"\033]1337;File="
          f"name={b64_name}"
          f"size={len(image_binary)};"
          f"width={image_side_len if isinstance(image_side_len, int) else image_side_len[0]}px;"
          f"height={image_side_len if isinstance(image_side_len, int) else image_side_len[1]}px;"
          f"inline=1:{b64_img}\a")


def show_image_by_store_url(store_url: str, img_wh: int = None):
    _, _, _, _, image_url = get_orig_img_url(store_url, print_log=False)
    image_binary = get_img_binary(change_img_url_size(image_url, img_wh) if img_wh else image_url)
    show_image_in_terminal("", image_binary, img_wh)


def async_submit_store_urls(store_urls: [str]):
    tasks = []
    for each_url in store_urls:
        tasks.append(asyncio.ensure_future(async_get_orig_img_url(each_url, print_log=False)))
    return asyncio.get_event_loop(), tasks


def async_wait_tasks(loop, tasks: list):
    results = loop.run_until_complete(asyncio.gather(*tasks))
    return results


def horizontal_show_image_by_store_urls(image_urls: Union[List[str], Tuple[str]]):
    images = [Image.open(BytesIO(get_img_binary(each_url))) for each_url in image_urls]
    long_img = concat_image(images)
    long_img_as_bytes = BytesIO()
    long_img.save(long_img_as_bytes, format='png')
    long_img_as_bytes = long_img_as_bytes.getvalue()
    show_image_in_terminal("", long_img_as_bytes, long_img.size)


def get_img_binary(image_url) -> bytes:
    return request.urlopen(image_url).read()


def get_img_maxsize(image_url_orig):
    # make sure to get largest/chosen icon size
    print('determining largest image size...')
    # AppStore will provide the possible largest size
    image_url_10240x0w = re.sub(r'230x0w', '10240x0w', image_url_orig)
    img_bin = get_img_binary(image_url_10240x0w)
    img_size_tup = Image.open(BytesIO(img_bin)).size
    print(f'image size is: {img_size_tup}')
    return image_url_10240x0w, img_bin, img_size_tup


def change_img_url_size(image_url_10240x0w, img_size: int):
    return re.sub(r"[0-9]+x0w", f'{img_size}x0w', image_url_10240x0w)


def get_orig_img_url(app_url, print_log: bool = True):
    # match App Store URLs
    match = re.search(r"(apps\.apple\.com/([a-z]{2})/app/)(.*/)?(id[0-9]+)", app_url)
    # groups() example output: ('apps.apple.com/us/app/', 'us', 'google/', 'id284815942')
    if not match:
        raise ValueError("invalid App Store URL!")
    # enforce https
    app_url_cleaned = r'https://' + match.group(1) + match.group(4)
    store_region = match.group(2)
    # try reg match
    try:
        with request.urlopen(app_url_cleaned) as response:
            web_html = response.read().decode()
    except urllib.error.HTTPError:
        raise ValueError("AppStore:")
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
    return app_name, app_url_cleaned, app_version, img_ext, img_url_orig


# TODO deduplicate
async def async_get_orig_img_url(store_url: str, print_log: bool = True):
    # match App Store URLs
    print(store_url)
    match = re.search(r"(apps\.apple\.com/([a-z]{2})/app/)(.*/)?(id[0-9]+)", store_url)
    # groups() example output: ('apps.apple.com/us/app/', 'us', 'google/', 'id284815942')
    if not match:
        raise ValueError("invalid App Store URL!")
    # enforce https
    app_url_cleaned = r'https://' + match.group(1) + match.group(4)
    store_region = match.group(2)
    # try reg match
    try:
        # with request.urlopen(app_url_cleaned) as response:
        #     web_html = response.read().decode()
        async with ClientSession() as session:
            async with session.get(app_url_cleaned) as response:
                response = await response.read()
                response = response.decode()
                web_html = response
    except Exception as e:
        print(e)
        raise ValueError("AppStore:")
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
    return app_name, app_url_cleaned, app_version, img_ext, img_url_orig


def concat_image(images: [Image.Image]) -> Image.Image:
    widths, heights = zip(*(i.size for i in images))

    total_width = sum(widths)
    max_height = max(heights)
    avg_width = total_width / len(images)
    gap_size = int(avg_width * 0.1)

    new_img = Image.new('RGBA', (total_width + gap_size * (len(images) - 1), max_height), (255, 255, 255, 0))

    x_offset = 0
    for im in images:
        new_img.paste(im, (x_offset, 0))
        x_offset += im.size[0] + gap_size

    return new_img
