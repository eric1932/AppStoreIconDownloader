import asyncio
import re
from asyncio import Task
from typing import Union, TypedDict, Set, List
from urllib import request

import bs4
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup

from proxy import ALL_PROXY
from utils.url_util import clean_store_url


class AppIconCollection:
    # _DEFAULT_TYPE_PRIORITY = ['image/webp', 'image/png', 'image/jpeg']

    class Metadata(TypedDict):
        base_url: str
        original_type: str
        types: Set[str]
        resolutions: List[int]

    def __init__(self, app_store_url: str, html_page: str = None):
        self.store_url: str
        self.store_region: str
        self.html_page: Union[str, None] = html_page
        self._html_task: Union[Task, None] = None
        self._metadata: Union[AppIconCollection.Metadata, None] = None

        self.store_url, self.store_region = clean_store_url(app_store_url)

        if not html_page:
            # create async task to get web page html
            self._html_task = asyncio.create_task(self._get_page_html())
        else:
            # parse icon metadata in-place
            self._parse_icon_metadata()

    async def _get_page_html(self) -> None:
        """
        Get web page html
        This is optionally called by __init__
        """
        async with ClientSession(
                connector=ProxyConnector.from_url(ALL_PROXY) if ALL_PROXY else None
        ) as session:
            async with session.get(self.store_url) as resp:
                assert resp.status == 200
                self.html_page = await resp.text()
                self._parse_icon_metadata()

    async def await_html_task(self):
        if self._html_task:
            await self._html_task

    def _parse_icon_metadata(self) -> Metadata:
        """
        Parse icon metadata from html_response
        Get base_url, types('webp', 'png', 'jpeg'), and resolutions(123w)
        :return:
        """
        soup = BeautifulSoup(self.html_page, 'html.parser')
        tag_picture = soup.find('picture', attrs={
            'id': re.compile(r'ember\d+'),
            'class': 'we-artwork',
        })  # The very first result is the app icon itself
        img_sources = list(filter(lambda x: type(x) == bs4.Tag and x.name == 'source', tag_picture.contents))
        img_sources_flatten = sum([[x.split(' ') for x in each_source.attrs.get('srcset').split(', ')]
                                   for each_source in img_sources], [])
        one_url = img_sources_flatten[0][0]

        # final return
        types = {each_source.attrs.get('type')[6:] for each_source in img_sources}
        resolutions = sorted({int(r[:-1]) for (_, r) in img_sources_flatten})
        img_base_url = one_url[:len(one_url) - one_url[::-1].index('/') - 1]
        original_type = img_base_url[len(img_base_url) - img_base_url[::-1].index('.'):]

        self._metadata = {
            'base_url': img_base_url,
            'original_type': original_type,
            'types': types,
            'resolutions': resolutions,
        }
        return self._metadata

    def get_metadata(self):
        return self._metadata.copy()

    def get_url(self, type_: str = None, resolution: Union[int, str] = None):
        """
        Get icon url
        :param type_: 'webp', 'png', 'jpeg'
        :param resolution: any resolution in metadata or 'max'
        :return: direct url to the image at designated resolution
        """
        if not type_:
            type_ = self._metadata['original_type']
        if not resolution:
            resolution = self._metadata['resolutions'][-1]
        elif resolution == 'max':
            resolution = '102400'
        else:
            assert resolution.isdigit()

        return f"{self._metadata['base_url']}/{resolution}x0w.{type_}"

    def get_bin(self, type_: str = None, resolution: Union[int, str] = None):
        icon_url = self.get_url(type_, resolution)
        with request.urlopen(icon_url) as resp:
            return resp.read()

    async def get_bin_async(self, type_: str = None, resolution: Union[int, str] = None):
        icon_url = self.get_url(type_, resolution)
        async with ClientSession(
                connector=ProxyConnector.from_url(ALL_PROXY) if ALL_PROXY else None
        ) as session:
            async with session.get(icon_url) as resp:
                assert resp.status == 200
                return await resp.read()
