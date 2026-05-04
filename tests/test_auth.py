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
        with patch.dict(os.environ, {"BEXIO_API_TOKEN": ""}), \
             patch.dict(sys.modules, {"keyring": mock_kr}):
            with self.assertRaises(SystemExit):
                get_token()

    def test_keyring_import_error_falls_through(self):
        with patch.dict(os.environ, {"BEXIO_API_TOKEN": ""}), \
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
        with patch.dict(os.environ, {"BEXIO_API_TOKEN": ""}), \
             patch.dict(sys.modules, {"keyring": mock_kr}), \
             patch("sys.stdout", buf):
            cmd_auth_status(None)
        self.assertIn("No token", buf.getvalue())
