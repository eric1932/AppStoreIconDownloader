#!/usr/bin/env python3

import argparse
import os
import re
import ssl
import time
import urllib.request as request
from io import BytesIO

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# allow certificate from local issuer
ssl._create_default_https_context = ssl._create_unverified_context


def download_album_cover(album_url: str, print_only: bool, args_name: str = None, save_path: str = None):
    if not save_path:
        save_path = os.path.join(os.path.expanduser("~"), 'Downloads')
    # match App Store URLs
    match = re.search(r"(music\.apple\.com/([a-z]{2})/album/)(.*/)?([0-9]+)", album_url)
    # groups() example output: ('apps.apple.com/us/app/', 'us', 'google/', 'id284815942')
    if not match:
        print('invalid App Store URL!')
        exit(1)
    # enforce https
    album_url = r'https://' + match.group(1) + match.group(4)
    store_region = match.group(2)

    # get html source code
    # Way 1: python requests (not working)
    # jpg is loaded afterwards
    # with request.urlopen(album_url) as response:
    #     page_source = response.read().decode()
    # Way 2: start WebDriver
    chrome_op = Options()  # TODO
    chrome_op.add_argument('--headless')
    browser = webdriver.Chrome(options=chrome_op)  # TODO
    browser.get(album_url)
    time.sleep(5)  # empirical value TODO
    page_source = browser.page_source
    browser.close()
    # browser.quit()

    # try reg match
    # old way
    # https://is1-ssl.mzstatic.com/image/thumb/Music4/v4/02/73/8c/02738ce9-dddd-3068-5a7b-ddf15c1b9601/NW10103280.png/270x270bb.jpg
    # image_match = re.search(r"https://is[0-9]+-ssl.mzstatic.com/image/thumb/Music.*?.png/(.*?)bb.jpg", page_source)
    # new way
    image_match = re.findall(r"https://is[0-9]+-ssl.mzstatic.com/image/thumb.*?.jpg\s[0-9]{2,4}w", page_source)[-1]
    if not image_match:
        print('no matches found!')
        exit(1)
    print("found image url!")
    image_match = re.match(r".*?.jpg", image_match)

    # Get album title
    title_match = re.search(r"<h1 class=\"product-name.*?>\s+(.*?)\s+<!---->\s+</h1>", page_source)
    album_title = title_match.group(1)

    image_match_url = image_match.group()
    print('determining largest image size...')
    img = Image.open(BytesIO(request.urlopen(image_match_url).read()))
    print('image size: {0}'.format(img.size))
    if print_only:
        print('album title:', album_title)
        print('store url:', album_url)
        print('image url:', image_match_url)
    else:
        if args_name:
            album_title = args_name
        output_file_name = album_title + '_' + str(img.size[0]) + 'x' + str(img.size[1]) + 'bb.jpg'  # TODO
        print('saving cover to file \"' + output_file_name + '\"')
        with request.urlopen(image_match_url) as response, open(os.path.join(save_path, output_file_name), 'wb') as file:
            img_bin = response.read()
            file.write(img_bin)
        print('success!')


# test album url
# The legend of heroes: Sen no Kiseki
main_album_url = 'https://music.apple.com/jp/album/762966064'
# main_album_url = 'https://music.apple.com/jp/album/%E8%8B%B1%E9%9B%84%E4%BC%9D%E8%AA%AC-%E9%96%83%E3%81%AE%E8%BB%8C%E8%B7%A1-%E3%82%AA%E3%83%AA%E3%82%B8%E3%83%8A%E3%83%AB%E3%82%B5%E3%82%A6%E3%83%B3%E3%83%89%E3%83%88%E3%83%A9%E3%83%83%E3%82%AF/762966064'

if __name__ == '__main__':
    # command line interface
    parser = argparse.ArgumentParser(description='Download album covers from iTunes Store')
    parser.add_argument('url', metavar='URL', type=str, nargs='?', help='iTunes URL (apps.apple.com...)')
    parser.add_argument('name', type=str, nargs='?', help='Album name (mandatory)')
    parser.add_argument('--debug', action='store_true', help='print only instead of download')
    args = parser.parse_args()

    if args.url:
        main_album_url = args.url
    elif not args.debug:
        main_album_url = input("iTunes URL: ")
    else:
        # use built-in
        pass

    download_album_cover(main_album_url,
                         True if args.debug else False,
                         args_name=args.name)
