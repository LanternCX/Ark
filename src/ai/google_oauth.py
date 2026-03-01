"""Google OAuth helpers for Gemini browser login."""

from __future__ import annotations

from dataclasses import dataclass


GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_OAUTH_SCOPES = ("https://www.googleapis.com/auth/generative-language",)


@dataclass(frozen=True)
class GoogleOAuthSecrets:
    """Client secrets needed for installed-app OAuth flow."""

    client_id: str
    client_secret: str


def run_browser_oauth_login(
    client_id: str,
    client_secret: str,
    scopes: tuple[str, ...] = GOOGLE_OAUTH_SCOPES,
) -> str:
    """Run local browser OAuth and return refresh token."""
    oauth_secrets = GoogleOAuthSecrets(
        client_id=client_id.strip(),
        client_secret=client_secret.strip(),
    )
    if not oauth_secrets.client_id or not oauth_secrets.client_secret:
        raise ValueError("google client id and client secret are required")

    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_config(
        client_config={
            "installed": {
                "client_id": oauth_secrets.client_id,
                "client_secret": oauth_secrets.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": GOOGLE_TOKEN_URI,
            }
        },
        scopes=list(scopes),
    )
    credentials = flow.run_local_server(port=0)
    refresh_token = credentials.refresh_token or ""
    if not refresh_token:
        raise RuntimeError("google oauth login completed without refresh token")
    return refresh_token


def refresh_google_access_token(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    scopes: tuple[str, ...] = GOOGLE_OAUTH_SCOPES,
) -> str:
    """Refresh and return Google OAuth access token."""
    if not client_id.strip() or not client_secret.strip() or not refresh_token.strip():
        raise ValueError("google oauth credentials are required")

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=GOOGLE_TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
        scopes=list(scopes),
    )
    credentials.refresh(Request())
    access_token = credentials.token or ""
    if not access_token:
        raise RuntimeError("google oauth refresh returned empty access token")
    return access_token


def build_google_credentials(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    scopes: tuple[str, ...] = GOOGLE_OAUTH_SCOPES,
):
    """Build and refresh Google OAuth credentials object."""
    if not client_id.strip() or not client_secret.strip() or not refresh_token.strip():
        raise ValueError("google oauth credentials are required")

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=GOOGLE_TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
        scopes=list(scopes),
    )
    credentials.refresh(Request())
    return credentials
