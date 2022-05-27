import re


def clean_store_url(app_url) -> (str, str):
    """
    Clean app store url by removing unnecessary path of app name
    :param app_url: App Store url
    :return: (cleaned App Store url, store region)
    """

    # first, remove app name from url
    app_url_clean = re.sub(r"/app/(.*/)?id", "/app/id", app_url)
    # second, match to get store region & validate
    match = re.match(r"(https?://)?(apps\.apple\.com/([a-z]{2})/app/id\d+)", app_url_clean)
    if not match:
        raise ValueError("Invalid App Store URL!")

    app_url_cleaned = f'https://{match.group(2)}'  # enforce https
    store_region = match.group(3)
    return app_url_cleaned, store_region
