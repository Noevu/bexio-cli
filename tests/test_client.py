"""Tests for BexioClient."""

import io
import json
import sys
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from bexio.client import BexioClient


def _mock_urlopen(payload, status=200):
    body = json.dumps(payload).encode()
    mock = MagicMock()
    mock.read.return_value = body
    mock.__enter__ = lambda s: s
    mock.__exit__ = MagicMock(return_value=False)
    return patch("urllib.request.urlopen", return_value=mock)


class TestBexioClient(unittest.TestCase):
    def setUp(self):
        self.client = BexioClient("TEST_TOKEN")

    def test_bearer_token_header(self):
        captured = []

        def fake_urlopen(req, *a, **kw):
            captured.append(req.headers.get("Authorization"))
            mock = MagicMock()
            mock.read.return_value = b"[]"
            mock.__enter__ = lambda s: s
            mock.__exit__ = MagicMock(return_value=False)
            return mock

        with patch("urllib.request.urlopen", fake_urlopen):
            self.client.get("/kb_order")

        self.assertIn("Bearer TEST_TOKEN", captured)

    def test_get_builds_url(self):
        captured = []

        def fake_urlopen(req, *a, **kw):
            captured.append(req.full_url)
            mock = MagicMock()
            mock.read.return_value = b"{}"
            mock.__enter__ = lambda s: s
            mock.__exit__ = MagicMock(return_value=False)
            return mock

        with patch("urllib.request.urlopen", fake_urlopen):
            self.client.get("/kb_order/47")

        self.assertIn("api.bexio.com/2.0/kb_order/47", captured[0])

    def test_get_with_params(self):
        captured = []

        def fake_urlopen(req, *a, **kw):
            captured.append(req.full_url)
            mock = MagicMock()
            mock.read.return_value = b"[]"
            mock.__enter__ = lambda s: s
            mock.__exit__ = MagicMock(return_value=False)
            return mock

        with patch("urllib.request.urlopen", fake_urlopen):
            self.client.get("/kb_order", params={"is_recurring": "true", "limit": 100})

        self.assertIn("is_recurring=true", captured[0])
        self.assertIn("limit=100", captured[0])

    def test_none_params_excluded(self):
        captured = []

        def fake_urlopen(req, *a, **kw):
            captured.append(req.full_url)
            mock = MagicMock()
            mock.read.return_value = b"[]"
            mock.__enter__ = lambda s: s
            mock.__exit__ = MagicMock(return_value=False)
            return mock

        with patch("urllib.request.urlopen", fake_urlopen):
            self.client.get("/kb_order", params={"limit": 100, "status": None})

        self.assertNotIn("status", captured[0])

    def test_post_method(self):
        captured_method = []

        def fake_urlopen(req, *a, **kw):
            captured_method.append(req.get_method())
            mock = MagicMock()
            mock.read.return_value = b"{}"
            mock.__enter__ = lambda s: s
            mock.__exit__ = MagicMock(return_value=False)
            return mock

        with patch("urllib.request.urlopen", fake_urlopen):
            self.client.post("/kb_invoice/1/send")

        self.assertEqual(captured_method, ["POST"])

    def test_http_error_exits(self):
        err = urllib.error.HTTPError(
            url="https://api.bexio.com/2.0/kb_order",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=io.BytesIO(b"Unauthorized"),
        )
        with patch("urllib.request.urlopen", side_effect=err):
            with self.assertRaises(SystemExit) as ctx:
                self.client.get("/kb_order")
        self.assertIn("401", str(ctx.exception))

    def test_parses_json_response(self):
        payload = [{"id": 1, "title": "Test"}]
        with _mock_urlopen(payload):
            result = self.client.get("/kb_order")
        self.assertEqual(result, payload)

    def test_empty_response_returns_dict(self):
        mock = MagicMock()
        mock.read.return_value = b""
        mock.__enter__ = lambda s: s
        mock.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock):
            result = self.client.post("/kb_invoice/1/send")
        self.assertEqual(result, {})

    def test_get_pdf_decodes_base64_envelope(self):
        # Bexio's PDF endpoints return a JSON envelope {name,size,mime,content(base64)},
        # not raw bytes, and reject Accept: application/pdf with HTTP 415 — every
        # request must ask for application/json (NOE-3277).
        import base64

        pdf_bytes = b"%PDF-1.5 real pdf bytes"
        envelope = {
            "name": "invoice_47.pdf",
            "size": len(pdf_bytes),
            "mime": "application/pdf",
            "content": base64.b64encode(pdf_bytes).decode(),
        }
        captured = []

        def fake_urlopen(req, *a, **kw):
            captured.append(req.headers.get("Accept"))
            mock = MagicMock()
            mock.read.return_value = json.dumps(envelope).encode()
            mock.__enter__ = lambda s: s
            mock.__exit__ = MagicMock(return_value=False)
            return mock

        with patch("urllib.request.urlopen", fake_urlopen):
            data = self.client.get_pdf("/kb_invoice/47/pdf")

        self.assertEqual(captured, ["application/json"])
        self.assertEqual(data, pdf_bytes)


class TestVersion(unittest.TestCase):
    def test_version_matches_pyproject(self):
        # The `--version` flag reads bexio.__version__; keep it in lockstep with
        # pyproject so `bexio --version` is a trustworthy install gate (NOE-3277).
        import tomllib
        from pathlib import Path

        import bexio

        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        with open(pyproject, "rb") as f:
            declared = tomllib.load(f)["project"]["version"]
        self.assertEqual(bexio.__version__, declared)
