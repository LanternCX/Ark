# Google OAuth Setup For Gemini (Developer)

This guide explains how to register Google OAuth credentials and connect Ark Gemini OAuth mode.

## 1. Prepare Google Cloud Project

1. Open Google Cloud Console.
2. Create or select a project.
3. Enable Gemini API (Generative Language API).

## 2. Configure OAuth Consent Screen

1. Go to OAuth consent screen.
2. User type: `External`.
3. Fill app name and support email.
4. Keep publishing status in `Testing` during local integration.
5. Add your Google account under `Test users`.

If test user is missing, OAuth login returns access denied.

## 3. Create Desktop OAuth Client

1. Open Credentials.
2. Click Create Credentials -> OAuth client ID.
3. Application type: `Desktop app`.
4. Save generated `client_id` and `client_secret`.

## 4. Configure Ark TUI

Path:

1. `Settings`
2. `LLM Settings`
3. Choose `Google Gemini`
4. `Gemini authentication method` -> `google_oauth`

Then fill:

- `Google client id`
- `Google client secret`
- Confirm `Login with Google in browser now?`

After browser login succeeds, Ark stores refresh token in `<runtime-root>/.ark/config.json`.

## 5. Stored Credentials

Ark stores these values locally:

- `google_client_id`
- `google_client_secret`
- `google_refresh_token`

Treat `<runtime-root>/.ark/config.json` as sensitive. Do not commit or share it.

## 6. Common Errors

- `access_denied`: current account is not listed in OAuth test users.
- `invalid_client`: wrong client id/secret pair.
- Missing refresh token: OAuth flow completed but no offline token granted; run login again.
- Token refresh failure: revoked credentials or changed OAuth client secret.

## 7. SDKs Used

Ark uses Google official SDK packages:

- `google-auth`
- `google-auth-oauthlib`
- `google-genai`
