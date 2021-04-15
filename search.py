#!/usr/bin/env python3

# Name: App Store Icon Downloader
# Author: Eric Liu
# Email: zl36@illinois.edu
# Version: 1.1.0

import argparse
import os
import re
import signal
import sys
import urllib.parse
from sys import exit

from googleapiclient.discovery import build

from credentials import api_key, cse_id
from downloader import download_image
from image_util import submit_store_urls_to_async, wait_async_tasks, horizontal_show_image_by_store_urls

REGIONS = ['cn', 'us']

FLAG_ITERM = os.environ.get("TERM_PROGRAM") == "iTerm.app"


def sigint_handler(sig, frame):
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint_handler)

    parser = argparse.ArgumentParser(description='Search and Download app icon from App Store')
    parser.add_argument('keyword', type=str, nargs='...', help='keyword to search; leave empty to use prompt input')
    parser.add_argument('--lucky', action='store_true', help='use the first search result')
    parser.add_argument('--debug', action='store_true', help='print debug info (TODO to be implemented)')
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
    results = []
    for each in list(filter(lambda x: 'Mac App Store' not in x['title'],
                            search_result['items'])):  # filter Mac App Store pages
        match = re.match(r"https?://apps.apple.com/([a-z]{2})/app/",
                         each['link'])  # filter out other regions & /developer
        if match and match.group(1) in REGIONS:
            results.append(each)
    results = list(filter(lambda x: '?l=' not in x['link'], results))  # remove link with alternative language

    if len(results) == 0:
        exit(0)
    # create async request for getting images (for iTerm)
    (loop, async_img_tasks) = submit_store_urls_to_async(map(lambda x: x['link'], results), img_side_len=64) if FLAG_ITERM else (None, [])
    for i, each in enumerate(results):
        print(str(i+1) + ".\t" + each['title'].strip())
        print("\t" + urllib.parse.unquote(each['link']))
    if args.lucky:
        print("I'm feeling lucky!")
        chosen_num = 1
    else:
        if FLAG_ITERM:  # iTerm spec
            img_results = wait_async_tasks(loop, async_img_tasks)
            horizontal_show_image_by_store_urls(img_results)
        while True:
            chosen_num = input("select: ")
            try:
                chosen_num = int(chosen_num)
                if 1 <= chosen_num <= len(results):
                    break
            except ValueError as e:
                pass
    chosen_item = results[chosen_num - 1]

    download_image(chosen_item['link'], False)
