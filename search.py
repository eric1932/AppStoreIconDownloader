#!/usr/bin/env python3

# Name: App Store Icon Downloader
# Author: Eric Liu
# Email: zl36@illinois.edu
# Version: 1.0.7

import argparse
import re
import signal
import urllib.parse
from sys import exit

from googleapiclient.discovery import build

from credentials import api_key, cse_id
from downloader import download_image

REGIONS = ['cn', 'us']


def sigint_handler(sig, frame):
    exit(0)


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
    search_result = service.cse().list(q=kw, cx=cse_id).execute()
    if 'items' not in search_result.keys():
        print("No result found.")
        exit(0)

    # filter results
    result = []
    for each in list(filter(lambda x: 'Mac App Store' not in x['title'],
                            search_result['items'])):  # filter Mac App Store pages
        match = re.match(r"https?://apps.apple.com/([a-z]{2})/app/",
                         each['link'])  # filter out other regions & /developer
        if match and match.group(1) in REGIONS:
            result.append(each)
    result = list(filter(lambda x: '?l=' not in x['link'], result))  # remove link with alternative language

    if len(result) == 0:
        exit(0)
    for i, each in enumerate(result):
        print(str(i+1) + ".\t" + each['title'].strip())
        print("\t" + urllib.parse.unquote(each['link']))
    if args.lucky:
        print("I'm feeling lucky!")
        chosen_num = 1
    else:
        while True:
            chosen_num = input("select: ")
            try:
                chosen_num = int(chosen_num)
                if 1 <= chosen_num <= len(result):
                    break
            except ValueError as e:
                pass
    chosen_item = result[chosen_num - 1]

    download_image(chosen_item['link'], False)
