#!/usr/bin/env python3

# Name: App Store Icon Downloader
# Author: Eric Liu
# Email: zl36@illinois.edu
# Version: 1.0.4

import argparse
import os
import re
import ssl
import urllib.parse as parse
import urllib.request as request
from io import BytesIO

from PIL import Image

# allow certificate from local issuer
ssl._create_default_https_context = ssl._create_unverified_context

# Google on the AppStore (test app_url)
app_url = 'https://apps.apple.com/us/app/google/id284815942'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download app icon from App Store')
    parser.add_argument('url', metavar='URL', type=str, nargs='?', help='App Store URL (apps.apple.com...)')
    parser.add_argument('name', type=str, nargs='?', help='Application name (mandatory)')
    args = parser.parse_args()

    # default values
    download_or_print = True  # True to download; False to print
    save_dir = os.path.join(os.path.expanduser("~"), 'Downloads')

    app_url = args.url if args.url else input("App Store URL: ")
    # match App Store URLs
    match = re.findall(r"apps\.apple\.com/[a-z]{2}/app/.*/id[0-9]+", app_url)
    if len(match) == 0:
        print('invalid App Store URL!')
        exit(1)
    else:
        # encode app_url & enforce https
        app_url = r'https://' + parse.quote(match[0])

    # try reg match
    with request.urlopen(app_url) as response:
        web_source_code = response.read().decode('UTF-8')
    # alternative re match "https:\/\/is.*?-ssl\.mzstatic\.com\/image\/thumb\/.*?AppIcon.*?\.png\/230x0w\.png"
    image_match = re.findall(r"https:\/\/is.*?-ssl\.mzstatic\.com\/image\/thumb\/.*?\.png\/230x0w\.png",
                             web_source_code)
    if len(image_match) == 0:
        print('no matches found!')
        exit(1)
    else:
        print("found image url!")
    version_match = re.findall(r"<p class=\"l-column small-6 medium-12 whats-new__latest__version\">.*?</p>",
                               web_source_code)  # returns a list
    version = "NA"
    if len(version_match) != 0:
        version = version_match[0][65:][:-4]  # extract version info

    image_url_orig = image_match[0]
    # make sure to get largest icon size
    print('determining largest image size...')
    image_url_10240 = re.sub(r'230x0w', '10240x0w', image_url_orig)
    img = Image.open(BytesIO(request.urlopen(image_url_10240).read()))
    print('image size is: {0}'.format(img.size))
    image_url_max = re.sub(r'10240x0w', str(img.size[0]) + 'x0w', image_url_10240)
    if download_or_print:
        app_name = args.name if args.name else input("input App name: ")
        output_file_name = app_name + '_' + version + '_' + str(img.size[0]) + 'x0w.png'
        print('saving image to file \"' + output_file_name + '\"')
        with request.urlopen(image_url_max) as response, open(os.path.join(save_dir, output_file_name), 'wb') as file:
            img_bin = response.read()
            file.write(img_bin)
        print('success!')
    else:
        print('image url:')
        print(image_url_max)
