# r006 · preflight

STATUS=OK (UTC 2026-10-15 00:48:18)

## CLI
rc=0
Kaggle CLI 2.2.4

## Submissions CLI2.x (rc=1)
Authentication required to call the Kaggle API.

First, you will need a Kaggle account. You can sign up at
  https://www.kaggle.com/account/login

Recommended: log in with OAuth via a web-based authorization flow.
No token to manage; credentials are cached locally for you.
    kaggle auth login

If you'd rather not use OAuth, generate an API token at
  https://www.kaggle.com/settings/api  (click "Generate New Token" under "API")
and supply it to the CLI in one of these ways:

  Option A: Environment variable
    export KAGGLE_API_TOKEN=xxxxxxxxxxxxxx  # token copied from the settings UI

  Option B: API token file
    Save the token to ~/.kaggle/access_token


## Fallback: kaggle==1.5.12 (legacy auth)
pip rc=0
## Submissions CLI1.x (rc=1)
401 - Unauthorized

WNIOSEK: klucz odrzucony także przez 1.x → token nieaktualny.
## Zgłoszeń dziś: nieznane (kaggle competitions submissions failed:
401 - Unauthorized
)

