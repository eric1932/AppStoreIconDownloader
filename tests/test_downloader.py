import os
import re
import unittest

from downloader import download_image
from tests.commons import APP_STORE_US_GOOGLE, APP_STORE_US_STAPLES


class DownloaderTestCase(unittest.TestCase):
    def test_download_google(self):
        download_image(APP_STORE_US_GOOGLE,
                       print_only=False,
                       save_path='./')
        contain_google = list(filter(lambda x: "google" in x.lower(), os.listdir()))
        self.assertTrue(len(contain_google) > 0)
        self.assertIsNotNone(re.match(r"Google_[0-9.]+_[0-9]+x0w.(jpg|png)", contain_google[0]))
        # cleanup
        os.remove(contain_google[0])

    def test_download_staples(self):
        download_image(APP_STORE_US_STAPLES,
                       print_only=False,
                       save_path='./')
        contain_staples = list(filter(lambda x: "staples" in x.lower(), os.listdir()))
        self.assertTrue(len(contain_staples) > 0)
        self.assertIsNotNone(re.match(r"Staples.*?_[0-9.]+_[0-9]+x0w.(jpg|png)", contain_staples[0]))
        # cleanup
        os.remove(contain_staples[0])

    # TODO test 404 page


if __name__ == '__main__':
    unittest.main()
