#!/usr/bin/env python3

# Name: App Store Icon Downloader
# Author: Eric Liu
# Email: zl36@illinois.edu
# Version: 1.0.7

import argparse
import os
import re
import ssl
import urllib.request as request
import urllib.error
from io import BytesIO
from sys import exit

from PIL import Image

# allow certificate from local issuer
ssl._create_default_https_context = ssl._create_unverified_context


def download_image(app_url: str, print_only: bool, args_name: str = None, save_path: str = None):
    if not save_path:
        save_path = os.path.join(os.path.expanduser("~"), 'Downloads')
    # match App Store URLs
    match = re.search(r"(apps\.apple\.com/([a-z]{2})/app/)(.*/)?(id[0-9]+)", app_url)
    # groups() example output: ('apps.apple.com/us/app/', 'us', 'google/', 'id284815942')
    if not match:
        print('invalid App Store URL!')
        exit(1)
    # enforce https
    app_url = r'https://' + match.group(1) + match.group(4)
    store_region = match.group(2)

    # try reg match
    try:
        with request.urlopen(app_url) as response:
            web_html = response.read().decode()
    except urllib.error.HTTPError as e:
        print("AppStore:", e)
        exit(1)
    # alternative re match "https:\/\/is.*?-ssl\.mzstatic\.com\/image\/thumb\/.*?AppIcon.*?\.png\/230x0w\.png"
    # image_match = re.findall(r"https:\/\/is.*?-ssl\.mzstatic\.com\/image\/thumb\/.*?\.png\/230x0w\.png", web_html)
    image_match = re.search(r"https://is.*?-ssl\.mzstatic\.com/image/thumb/.*?\.(png|jpg|jpeg)/230x0w\.("
                            r"png|jpg|jpeg)", web_html)
    if not image_match:
        print('no matches found!')
        exit(1)
    print("found image url!")
    file_type = image_match.group(2)

    # Get app name
    if store_region == 'cn':
        app_name = re.search("<title>‎App\xa0Store 上的“(.*)”</title>", web_html).group(1)
    else:
        app_name = re.search("<title>\u200e(.*) on the App\xa0Store</title>", web_html).group(1)

    # Get app version
    # '<p class="l-column small-6 medium-12 whats-new__latest__version">Version 105.0</p>'
    if store_region == 'cn':
        app_version = re.search(r"whats-new__latest__version\"\s?(data-test-version-number)?>版本 (.*?)</p>",
                                web_html).group(2)
    else:
        app_version = re.search(r"whats-new__latest__version\"\s?(data-test-version-number)?>Version (.*?)</p>",
                                web_html).group(2)

    image_url_orig = image_match.group()
    # make sure to get largest icon size
    print('determining largest image size...')
    image_url_10240 = re.sub(r'230x0w', '10240x0w', image_url_orig)
    img = Image.open(BytesIO(request.urlopen(image_url_10240).read()))
    print('image size is: {0}'.format(img.size))
    image_url_max = re.sub(r'10240x0w', str(img.size[0]) + 'x0w', image_url_10240)
    if print_only:
        print('app name:', app_name)
        print('version:', app_version)
        print('store url:', app_url)
        print('image url:', image_url_max)
    else:
        if args_name:
            app_name = args_name
        output_file_name = app_name + '_' + app_version + '_' + str(img.size[0]) + 'x0w.' + file_type
        print('saving image to file \"' + output_file_name + '\"')
        with request.urlopen(image_url_max) as response, open(os.path.join(save_path, output_file_name), 'wb') as file:
            img_bin = response.read()
            file.write(img_bin)
        print('success!')


# test app url
# Google on the AppStore
main_app_url = 'https://apps.apple.com/us/app/google/id284815942'
# main_app_url = 'https://apps.apple.com/us/app/id284815942'
# WeChat
# main_app_url = 'https://apps.apple.com/us/app/wechat/id414478124'
# main_app_url = 'https://apps.apple.com/cn/app/wechat/id414478124'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download app icons from App Store')
    parser.add_argument('url', metavar='URL', type=str, nargs='?', help='App Store URL (apps.apple.com...)')
    parser.add_argument('name', type=str, nargs='?', help='Application name')
    parser.add_argument('--debug', action='store_true', help='print only instead of download')
    args = parser.parse_args()

    if args.url:
        main_app_url = args.url
    elif not args.debug:
        main_app_url = input("App Store URL: ")
    else:
        # use built-in
        pass

    download_image(main_app_url,
                   args.debug,
                   args_name=args.name)
