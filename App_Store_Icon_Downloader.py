#!/usr/bin/env python3

# Name: App Store Icon Downloader
# Author: Eric Liu
# Email: zl36@illinois.edu
# Version: 1.0.3

import os
import re
import ssl
import sys
import urllib.parse as parse
import urllib.request as request
from io import BytesIO

from PIL import Image

# allow certificate from local issuer
ssl._create_default_https_context = ssl._create_unverified_context

# Google on the AppStore | default app_url
app_url = 'https://apps.apple.com/us/app/google/id284815942'

if __name__ == '__main__':
    # default values
    use_custom_url = True
    download_or_else_print = True
    save_dir = os.path.expanduser("~") + '/Downloads'

    if use_custom_url:
        app_url = input("App Store URL: ")
        # restrict to US or CN App Store
        match = re.findall(r"http(s)?://apps\.apple\.com/(us|cn)/app/.*?/id[0-9].*", app_url)
        if len(match) == 0:
            print('invalid App Store URL!')
            sys.exit(1)

    # url-encode app_url & enforce https
    app_url = r'https://' + parse.quote(re.findall(r"apps\.apple\.com.*", app_url)[0])

    # try reg match
    with request.urlopen(app_url) as response:
        web_source_code = response.read().decode('UTF-8')
    # alternative re match "https:\/\/is.*?-ssl\.mzstatic\.com\/image\/thumb\/.*?AppIcon.*?\.png\/230x0w\.png"
    image_match = re.findall(r"https:\/\/is.*?-ssl\.mzstatic\.com\/image\/thumb\/.*?\.png\/230x0w\.png",
                             web_source_code)
    if len(image_match) == 0:
        print('no matches found!')
        sys.exit(1)
    else:
        print("found image url!")
    version_match = re.findall(r"<p class=\"l-column small-6 medium-12 whats-new__latest__version\">.*?</p>",
                               web_source_code)  # returns a list
    version = "None"
    if len(version_match) != 0:
        version = version_match[0][65:][:-4]  # extract version info

    image_url_orig = image_match[0]
    # make sure to get largest icon size
    print('determining largest image size...')
    image_url_10240 = re.sub(r'230x0w', '10240x0w', image_url_orig)
    img = Image.open(BytesIO(request.urlopen(image_url_10240).read()))
    print('image size is: {0}'.format(img.size))
    image_url_max = re.sub(r'10240x0w', str(img.size[0]) + 'x0w', image_url_10240)
    if download_or_else_print:
        app_name = input("input App name: ")
        output_file_name = app_name + '_' + version + '_' + str(img.size[0]) + 'x0w.png'
        print('saving image to file \"' + output_file_name + '\"')
        with request.urlopen(image_url_max) as response, open(os.path.join(save_dir, output_file_name), 'wb') as file:
            img_bin = response.read()
            file.write(img_bin)
        print('success!')
    else:
        print('image url:')
        print(image_url_max)
