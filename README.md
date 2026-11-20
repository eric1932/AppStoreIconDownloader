# App Store Icon Downloader

Download App Store app icons at full resolution, usually 1024×1024. You can start from an App Store link, an app id, or a search.

It uses Apple's public iTunes Search and Lookup API, so you don't need an API key.

## Install

Install [uv](https://docs.astral.sh/uv/) first, then:

```shell
uv tool install git+https://github.com/eric1932/AppStoreIconDownloader
```

That puts an `appicon` command on your `PATH`. To update it later, run `uv tool upgrade appicon`.

## Usage

### Download from a link or id

```shell
appicon get https://apps.apple.com/us/app/google/id284815942
appicon get 414478124 --country cn
appicon get id284815942 --size 512 --format jpg --output ./icons
appicon get id284815942 --dry-run    # show the app and the icon URL, download nothing
```

- **Where it saves:** `~/Downloads` by default, with names like `Google_447.9_1024x1024.png`.
- **Which storefront:** `--country` if you give it, otherwise the one in the link, otherwise `us`.
- **Size:** the full-size original unless you set `--size`.
- **Existing files:** a file with the same name is overwritten.

### Search and download

```shell
appicon search google maps             # searches the us and cn stores
appicon search wechat -c cn --lucky    # download the first hit without asking
```

The command lists the results and asks which one to download. In iTerm2 it also shows the icons inline.

### Proxy

`HTTPS_PROXY` and `ALL_PROXY` are honoured, including `socks5://` URLs. You can also pass a proxy directly with `--proxy socks5://127.0.0.1:1080`.

Run `appicon get --help` or `appicon search --help` to see every option.

## Development

The code lives in `src/appicon/` and the project is managed with uv:

| Module | Role |
| --- | --- |
| `cli.py` | The `appicon` command. Parses arguments and prints results. |
| `preview.py` | iTerm2 inline images. |
| `service.py` | `IconService`, which resolves, searches and downloads. |
| `clients.py` | `ItunesClient`, built on httpx, with timeouts and retries. |
| `models.py`, `artwork.py` | Data types and pure helpers. They do no IO. |

```shell
uv sync                                      # create .venv with the dev tools
uv run pytest                                # unit tests, offline
uv run pytest -m network tests/regression    # downloads the real Google icon
uv run ruff check && uv run ruff format --check
uv run mypy                                  # strict type check
```

The unit tests replay recorded API responses from `tests/unit/fixtures/`. The regression tests talk to Apple directly. CI runs them on every pull request and once a week.
