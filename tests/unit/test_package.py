import appicon


def test_version_matches_installed_metadata() -> None:
    assert appicon.__version__ == "2.0.0"
