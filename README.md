# App Store Icon Downloader
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
2. Create `credentials.py` and fill in as following
```python
cse_id = '<CSE ID>'
api_key = '<API Key>'
```
3. run `search.py`