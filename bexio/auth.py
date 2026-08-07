"""Token resolution: explicit env var → live token command → keyring → error.

Why a token command sits ABOVE the keyring: a token stored once goes stale. OAuth
access tokens expire hourly and nothing refreshes a keyring copy, so `bexio auth
login` produces a snapshot that dies within the hour. On 2026-08-07 the stored
token was a 2199-char JWT and every call returned HTTP 401. That is the same shape
as the 2026-08-03 incident, where reading a stored token directly served a REVOKED
one to every caller for weeks — the lesson there was: never let a stored copy win
over a live provider.

Set the command once, e.g. in the shell profile:

    export BEXIO_TOKEN_COMMAND='cd ~/projects/noevu-company/scripts/finance && python3 bexio_auth.py token'

`BEXIO_API_TOKEN` still wins over everything as an explicit per-invocation override.
A failing command WARNS on stderr and falls through to the keyring — a broken
provider must be visible, not silently papered over with a stale token.
"""

import getpass
import os
import subprocess
import sys

KEYRING_SERVICE = "bexio-cli"
KEYRING_USERNAME = "api-token"
ENV_VAR = "BEXIO_API_TOKEN"
TOKEN_COMMAND_ENV = "BEXIO_TOKEN_COMMAND"
COMMAND_TIMEOUT = 30


def _token_from_command() -> str:
    """Run the configured provider command and return its stdout, or "" to fall through."""
    command = os.environ.get(TOKEN_COMMAND_ENV, "").strip()
    if not command:
        return ""
    try:
        result = subprocess.run(command, shell=True, capture_output=True,
                                text=True, timeout=COMMAND_TIMEOUT)
    except Exception as e:
        print(f"warning: {TOKEN_COMMAND_ENV} could not be run ({e}) — falling back.",
              file=sys.stderr)
        return ""
    token = (result.stdout or "").strip()
    if result.returncode != 0 or not token:
        detail = (result.stderr or "").strip().splitlines()
        hint = detail[-1] if detail else f"exit {result.returncode}, no output"
        print(f"warning: {TOKEN_COMMAND_ENV} failed ({hint}) — falling back to the "
              f"stored token, which may be stale.", file=sys.stderr)
        return ""
    return token


def _token_from_keyring() -> str:
    try:
        import keyring
        return (keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME) or "").strip()
    except Exception:
        return ""


def get_token() -> str:
    token = os.environ.get(ENV_VAR, "").strip()
    if token:
        return token

    token = _token_from_command()
    if token:
        return token

    token = _token_from_keyring()
    if token:
        return token

    sys.exit(
        f"No API token found.\n"
        f"  Live provider (preferred):  export {TOKEN_COMMAND_ENV}='<command printing a token>'\n"
        f"  One-off:                    export {ENV_VAR}=<token>\n"
        f"  Stored copy (goes stale):   bexio auth login"
    )


def store_token(token: str) -> None:
    try:
        import keyring
        keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, token)
    except Exception as e:
        sys.exit(f"Failed to store token in keyring: {e}\nSet {ENV_VAR} env var instead.")


def delete_token() -> None:
    try:
        import keyring
        keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except Exception:
        pass


def cmd_auth_login(args) -> None:
    token = getpass.getpass("Bexio API token: ").strip()
    if not token:
        sys.exit("No token entered.")
    store_token(token)
    print("Token stored.")


def cmd_auth_logout(args) -> None:
    delete_token()
    print("Token removed.")


def cmd_auth_status(args) -> None:
    """Report the source that get_token() would actually use, in that order.

    Reporting the keyring while a live command is configured sent the 2026-08-07
    debugging down the wrong path ("Token found in keyring, length 2199" — while the
    real problem was that the stored copy had expired). Status must mirror
    resolution order, or it misleads exactly when it matters.
    """
    token = os.environ.get(ENV_VAR, "").strip()
    if token:
        print(f"Token set via {ENV_VAR} (length: {len(token)}) — explicit override.")
        return

    command = os.environ.get(TOKEN_COMMAND_ENV, "").strip()
    if command:
        fresh = _token_from_command()
        if fresh:
            print(f"Token from {TOKEN_COMMAND_ENV} (length: {len(fresh)}) — live, "
                  f"refreshed per call.")
            print(f"  command: {command}")
            return
        print(f"{TOKEN_COMMAND_ENV} is set but produced no token — see the warning above.")

    stored = _token_from_keyring()
    if stored:
        print(f"Token found in keyring (length: {len(stored)}).")
        print(f"  WARNING: a stored token does not refresh. If calls return HTTP 401 "
              f"it has expired — configure {TOKEN_COMMAND_ENV} instead.")
        return
    print(f"No token configured.\n"
          f"  Preferred: export {TOKEN_COMMAND_ENV}='<command printing a token>'\n"
          f"  Or:        bexio auth login")
