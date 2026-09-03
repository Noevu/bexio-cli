"""Tests for auth module."""

import io
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from bexio.auth import get_token, store_token, delete_token, cmd_auth_status


class TestGetToken(unittest.TestCase):
    def test_env_var_takes_priority(self):
        with patch.dict(os.environ, {"BEXIO_API_TOKEN": "env_token"}):
            self.assertEqual(get_token(), "env_token")

    def test_env_var_stripped(self):
        with patch.dict(os.environ, {"BEXIO_API_TOKEN": "  token123  "}):
            self.assertEqual(get_token(), "token123")

    def test_keyring_fallback(self):
        mock_kr = MagicMock()
        mock_kr.get_password.return_value = "keyring_token"
        with patch.dict(os.environ, {}, clear=True), \
             patch.dict(sys.modules, {"keyring": mock_kr}), \
             patch("bexio.auth.os.environ.get", return_value=""):
            token = get_token()
        self.assertEqual(token, "keyring_token")

    def test_no_token_exits(self):
        mock_kr = MagicMock()
        mock_kr.get_password.return_value = None
        with patch.dict(os.environ, {"BEXIO_API_TOKEN": ""}, clear=True), \
             patch.dict(sys.modules, {"keyring": mock_kr}):
            with self.assertRaises(SystemExit):
                get_token()

    def test_keyring_import_error_falls_through(self):
        with patch.dict(os.environ, {"BEXIO_API_TOKEN": ""}, clear=True), \
             patch("builtins.__import__", side_effect=ImportError):
            with self.assertRaises(SystemExit):
                get_token()


class TestAuthStatus(unittest.TestCase):
    def test_shows_env_var_source(self):
        buf = io.StringIO()
        with patch.dict(os.environ, {"BEXIO_API_TOKEN": "tok"}), \
             patch("sys.stdout", buf):
            cmd_auth_status(None)
        self.assertIn("BEXIO_API_TOKEN", buf.getvalue())

    def test_shows_no_token_message(self):
        mock_kr = MagicMock()
        mock_kr.get_password.return_value = None
        buf = io.StringIO()
        with patch.dict(os.environ, {"BEXIO_API_TOKEN": ""}, clear=True), \
             patch.dict(sys.modules, {"keyring": mock_kr}), \
             patch("sys.stdout", buf):
            cmd_auth_status(None)
        self.assertIn("No token", buf.getvalue())


class TestTokenCommandBeatsStoredToken(unittest.TestCase):
    """A token stored once goes stale: OAuth access tokens expire hourly, and
    nothing refreshes a keyring copy. On 2026-08-07 the stored token was a 2199-char
    JWT and every call returned HTTP 401 — the same failure mode that served a
    revoked PAT to every caller for weeks in the 2026-08-03 incident.

    So a configured live provider (BEXIO_TOKEN_COMMAND) must WIN over the stored
    copy. The explicit per-invocation override BEXIO_API_TOKEN still wins over both.
    A failing provider warns loudly instead of silently handing back a stale token."""

    def test_command_output_is_used_and_stripped(self):
        with patch.dict(os.environ, {"BEXIO_TOKEN_COMMAND": "echo '  fresh_token  '"}, clear=True):
            self.assertEqual(get_token(), "fresh_token")

    def test_explicit_env_token_still_wins_over_the_command(self):
        with patch.dict(os.environ, {"BEXIO_API_TOKEN": "explicit",
                                     "BEXIO_TOKEN_COMMAND": "echo from_command"}, clear=True):
            self.assertEqual(get_token(), "explicit")

    def test_command_beats_the_stored_keyring_token(self):
        mock_kr = MagicMock()
        mock_kr.get_password.return_value = "stale_keyring_token"
        with patch.dict(os.environ, {"BEXIO_TOKEN_COMMAND": "echo fresh"}, clear=True), \
             patch.dict(sys.modules, {"keyring": mock_kr}):
            self.assertEqual(get_token(), "fresh")

    def test_failing_command_warns_then_falls_back_to_keyring(self):
        mock_kr = MagicMock()
        mock_kr.get_password.return_value = "keyring_token"
        err = io.StringIO()
        with patch.dict(os.environ, {"BEXIO_TOKEN_COMMAND": "exit 3"}, clear=True), \
             patch.dict(sys.modules, {"keyring": mock_kr}), \
             patch("sys.stderr", err):
            self.assertEqual(get_token(), "keyring_token")
        self.assertIn("BEXIO_TOKEN_COMMAND", err.getvalue())

    def test_error_message_mentions_the_command_option(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch("bexio.auth._token_from_keyring", return_value=""):
            with self.assertRaises(SystemExit) as ctx:
                get_token()
        self.assertIn("BEXIO_TOKEN_COMMAND", str(ctx.exception))
