import pytest

from ark.ai.google_oauth import refresh_google_access_token, run_browser_oauth_login


def test_run_browser_oauth_login_requires_client_secrets() -> None:
    with pytest.raises(ValueError):
        run_browser_oauth_login(client_id="", client_secret="")


def test_refresh_google_access_token_requires_all_fields() -> None:
    with pytest.raises(ValueError):
        refresh_google_access_token(
            client_id="",
            client_secret="",
            refresh_token="",
        )
