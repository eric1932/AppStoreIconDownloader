import re
import unittest

from appstore_parser import get_orig_img_url
from tests.commons import APP_STORE_US_GOOGLE


class ImageUtilTestCase(unittest.TestCase):
    def test_parser(self):
        app_name, app_url_cleaned, app_version, img_ext, img_url_orig = get_orig_img_url(APP_STORE_US_GOOGLE,
                                                                                         print_log=False)
        print(app_name, app_url_cleaned, app_version, img_ext, img_url_orig)
        self.assertEqual(app_name, "Google")
        self.assertEqual(app_url_cleaned, "https://apps.apple.com/us/app/id284815942")
        self.assertIsNotNone(app_version)
        self.assertTrue(img_ext in ("png", "jpg"))
        self.assertIsNotNone(re.match(r"https?://is[0-9]+-ssl\.mzstatic.com/image/.*x0w.(jpg|png)", img_url_orig))


if __name__ == '__main__':
    unittest.main()
