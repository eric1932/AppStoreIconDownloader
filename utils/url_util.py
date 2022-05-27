import re


def clean_store_url(app_url) -> (str, str):
    """
    Clean app store url by removing unnecessary path of app name
    :param app_url: App Store url
    :return: cleaned App Store url and store region
    """

    # match App Store URLs
    match = re.search(r"(apps\.apple\.com/([a-z]{2})/app/)(.*/)?(id[0-9]+)", app_url)
    # groups() example output: ('apps.apple.com/us/app/', 'us', 'google/', 'id284815942')
    if not match:
        raise ValueError("invalid App Store URL!")
    # enforce https
    app_url_cleaned = r'https://' + match.group(1) + match.group(4)
    store_region = match.group(2)
    return app_url_cleaned, store_region
