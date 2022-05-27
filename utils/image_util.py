import asyncio
import base64
import re
from io import BytesIO
from typing import Union, List, Tuple
from urllib import request as request

from PIL import Image
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector

from appstore_parser import async_get_orig_img_url
from Constants import IMAGE_SIZE_CEIL
from proxy import ALL_PROXY


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


# unused
# def show_image_by_store_url(store_url: str, img_wh: int = None):
#     _, _, _, _, image_url = get_orig_img_url(store_url, print_log=False)
#     image_binary = get_img_binary(change_img_url_size(image_url, img_wh) if img_wh else image_url)
#     show_image_in_terminal("", image_binary, img_wh)


def submit_store_urls_to_async(store_urls: [str], img_side_len: int = None):
    tasks = []
    for each_url in store_urls:
        tasks.append(asyncio.ensure_future(async_get_icon_by_url(each_url, print_log=False, size=img_side_len)))
    return asyncio.get_event_loop(), tasks


def wait_async_tasks(loop, tasks: list):
    results = loop.run_until_complete(asyncio.gather(*tasks))
    return results


async def async_get_icon_by_url(store_url: str, print_log: bool = True, size: int = None):
    _, _, _, _, img_url_orig = await async_get_orig_img_url(store_url, print_log)

    if img_url_orig:
        async with ClientSession(connector=ProxyConnector.from_url(ALL_PROXY)) if ALL_PROXY \
                else ClientSession() as session:
            async with session.get(change_img_url_size(img_url_orig, size) if size else img_url_orig) as response:
                response = await response.read()
                image_bin = response
    else:
        # compose empty image
        image = Image.new('RGBA', (size if size else 128, size if size else 128), (255, 255, 255, 0))
        image_as_bytes = BytesIO()
        image.save(image_as_bytes, format='png')
        image_bin = image_as_bytes.getvalue()

    return image_bin


# TODO auto new line given console width
def horizontal_show_image_by_store_urls(image_bytes: Union[List[bytes], Tuple[bytes]]):
    images = [Image.open(BytesIO(each_bytes)) for each_bytes in image_bytes]
    long_img = concat_image(images)
    long_img_as_bytes = BytesIO()
    long_img.save(long_img_as_bytes, format='png')
    long_img_as_bytes = long_img_as_bytes.getvalue()
    show_image_in_terminal("", long_img_as_bytes, long_img.size)


def get_img_maxsize(image_url_orig):
    # make sure to get largest/chosen icon size
    print('determining largest image size...')
    # AppStore will provide the possible largest size
    image_url_10240x0w = re.sub(r'230x(0w|172sr)',
                                f'{IMAGE_SIZE_CEIL}x0w',
                                image_url_orig)  # also match for iMessage icon
    img_bin = request.urlopen(image_url_10240x0w).read()
    img_size_tup = Image.open(BytesIO(img_bin)).size
    print(f'image size is: {img_size_tup}')
    return image_url_10240x0w, img_bin, img_size_tup


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


def change_img_url_size(image_url_XxY, img_size: int):
    return re.sub(r"[0-9]+x(0w|[0-9]+sr)", f'{img_size}x0w', image_url_XxY)