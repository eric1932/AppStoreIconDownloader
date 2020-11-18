#!/usr/bin/env python3

# Name: App Store Icon Downloader
# Author: Eric Liu
# Email: zl36@illinois.edu
# Version: 1.0.7

import argparse
import signal
import sys
import urllib.parse

from googleapiclient.discovery import build

from credentials import api_key, cse_id
from downloader import download_image


def sigint_handler(sig, frame):
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint_handler)

    parser = argparse.ArgumentParser(description='Search and Download app icon from App Store')
    parser.add_argument('keyword', type=str, nargs='?', help='keyword to search; leave empty to use prompt input')
    parser.add_argument('--lucky', action='store_true', help='use the first search result')
    args = parser.parse_args()

    if args.keyword:
        kw = args.keyword
    else:
        kw = input("search keyword: ")

    service = build("customsearch", "v1", developerKey=api_key)
    result = service.cse().list(q=kw, cx=cse_id).execute()
    if 'items' not in result.keys():
        print("No results found.")
        exit(0)
    result = list(filter(lambda x: 'Mac App Store' not in x['title'], result['items']))  # filter Mac App Store pages
    if len(result) == 0:
        exit(0)
    for i, each in enumerate(result):
        print(str(i+1) + ". " + each['title'])
        print("\t" + urllib.parse.unquote(each['link']))
    if args.lucky:
        print("I'm feeling lucky!")
        chosen_nb = 1
    else:
        while True:
            chosen_nb = input("select: ")
            try:
                chosen_nb = int(chosen_nb)
                if 1 <= chosen_nb <= len(result):
                    break
            except ValueError as e:
                pass
    chosen_item = result[chosen_nb-1]

    download_image(chosen_item['link'], False)
