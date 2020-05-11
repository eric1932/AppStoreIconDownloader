import urllib.parse

from googleapiclient.discovery import build

from credentials import api_key, cse_id
from downloader import download_image

if __name__ == '__main__':
    service = build("customsearch", "v1", developerKey=api_key)
    result = service.cse().list(q=input("search kw: "), cx=cse_id).execute()
    result = list(filter(lambda x: 'Mac App Store' not in x['title'], result['items']))  # filter Mac App Store pages
    if len(result) == 0:
        exit(0)
    for i, each in enumerate(result):
        print(str(i+1) + ". " + each['title'])
        print("\t" + urllib.parse.unquote(each['link']))
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
