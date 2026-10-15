# r005 · preflight

STATUS=FAILED (UTC 2026-10-15 00:47:24)

BŁĄD: kaggle competitions submissions failed:
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


TRACEBACK:
Traceback (most recent call last):
  File "/home/runner/work/Smak-Domu-Konkurs/Smak-Domu-Konkurs/arc-agi-3/kaggle/ops/ops.py", line 143, in main
    text = OPS[op_name](args, out_dir)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/Smak-Domu-Konkurs/Smak-Domu-Konkurs/arc-agi-3/kaggle/ops/ops.py", line 67, in op_preflight
    today = todays_submissions()
            ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/Smak-Domu-Konkurs/Smak-Domu-Konkurs/arc-agi-3/kaggle/ops/ops.py", line 47, in todays_submissions
    raise RuntimeError(f"kaggle competitions submissions failed:\n{out}")
RuntimeError: kaggle competitions submissions failed:
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


