#!/usr/bin/env python3

# Name: App Store Icon Downloader
# Author: Eric Liu
# Email: zl36@illinois.edu
# Version: 1.1.0

import argparse
import os
import ssl
import urllib.error
from io import BytesIO
from sys import stderr
from urllib import request

from PIL import Image

from appstore_parser import get_orig_img_url
from utils.image_util import show_image_in_terminal, get_img_maxsize, change_img_url_size

# disable verifications to allow certificate from local issuer

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def download_image(app_url: str, print_only: bool = False, args_name: str = None, save_path: str = None):
    if not save_path:
        save_path = os.path.join(os.path.expanduser("~"), 'Downloads')

    try:
        app_name, app_url_cleaned, app_version, img_ext, image_url_orig = get_orig_img_url(app_url)
    except urllib.error.HTTPError and ValueError:
        # 404 not found
        print("Error 404: Page Not Found", file=stderr)
        print("Nothing is downloaded!", file=stderr)
        return

    image_url_10240x0w, img_bin, img_size_tup = get_img_maxsize(image_url_orig)

    if os.environ.get("TERM_PROGRAM") == "iTerm.app":  # iTerm spec
        image_url_128 = change_img_url_size(image_url_10240x0w, 128)
        with request.urlopen(image_url_128) as resp:
            image_bin_128 = resp.read()
        show_image_in_terminal(app_name, image_bin_128, Image.open(BytesIO(image_bin_128)).size)

    if print_only:
        print('app name:', app_name)
        print('version:', app_version if app_version else "[N/A]")
        print('store url:', app_url_cleaned)
        print('image url:', change_img_url_size(image_url_10240x0w, img_size_tup[0]))
    else:
        if args_name:
            app_name = args_name
        output_file_name = app_name + (('_' + app_version) if app_version else '') + '_' + str(img_size_tup[0]) + (
            'x0w' if img_size_tup[0] == img_size_tup[1] else f'x{str(img_size_tup[1])}') + '.' + img_ext
        print('saving image to file \"' + output_file_name + '\"')
        with open(os.path.join(save_path, output_file_name), 'wb') as file:
            file.write(img_bin)
        print('success!')


# test app url
# Google on the AppStore
main_app_url = 'https://apps.apple.com/us/app/google/id284815942'
# main_app_url = 'https://apps.apple.com/us/app/id284815942'
# WeChat
# main_app_url = 'https://apps.apple.com/us/app/wechat/id414478124'
# main_app_url = 'https://apps.apple.com/cn/app/wechat/id414478124'
# iMessage app
main_app_url = 'https://apps.apple.com/us/app/id1152347024'
# No png
main_app_url = 'https://apps.apple.com/us/app/id1121100236'

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
