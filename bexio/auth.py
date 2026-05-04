"""Token resolution: env var → keyring → error."""

import getpass
import os
import sys

KEYRING_SERVICE = "bexio-cli"
KEYRING_USERNAME = "api-token"
ENV_VAR = "BEXIO_API_TOKEN"


def get_token() -> str:
    token = os.environ.get(ENV_VAR, "").strip()
    if token:
        return token

    try:
        import keyring
        token = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME) or ""
        if token.strip():
            return token.strip()
    except Exception:
        pass

    sys.exit(
        f"No API token found.\n"
        f"  Run:  bexio auth login\n"
        f"  Or:   export {ENV_VAR}=<token>"
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
    token = os.environ.get(ENV_VAR, "").strip()
    if token:
        print(f"Token set via {ENV_VAR} (length: {len(token)})")
        return
    try:
        import keyring
        stored = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
        if stored:
            print(f"Token found in keyring (length: {len(stored)})")
            return
    except Exception:
        pass
    print("No token configured. Run: bexio auth login")
