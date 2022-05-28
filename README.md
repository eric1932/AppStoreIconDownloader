# App Store Icon Downloader

## Setup
First, you need to create your own Google Programmable Search Engine (CSE) API and the **API key** to access it.

Using a custom search engine can help narrowing the result to only the App Store.

To create the search engine, open [this link](https://cse.google.com/cse/create/new)
- Fill `apps.apple.com` in the "Sites to search" section
- Language can be any
- Name your search engine

Save the `Search engine ID`.

Next, create a new project in [Google Cloud Platform](https://console.cloud.google.com/projectcreate?organizationId=0&authuser=0)

Go to [Marketplace](https://console.cloud.google.com/marketplace/product/google/customsearch.googleapis.com) and enable `Custom Search API` for this project.

Go to [API and service](https://console.cloud.google.com/apis/credentials)

Click on `Create credential` -> `Create API key`. This is the API key we want to use.

Finally, create `.env` and fill as follows
```dotenv
CSE_ID='<CSE ID>'
API_KEY='<API Key>'
```

## Usage
### Download icons directly from urls
```shell script
usage: downloader.py [-h] [--debug] [URL] [name]

Download app icons from App Store

positional arguments:
  URL         App Store URL (apps.apple.com...)
  name        Application name

optional arguments:
  -h, --help  show this help message and exit
  --debug     print only instead of download
```
### Search & Download
1. Install requirements
2. Create `.env` and fill as follows
```dotenv
CSE_ID='<CSE ID>'
API_KEY='<API Key>'
```
3. run `search.py`