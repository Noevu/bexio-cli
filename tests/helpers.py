"""Shared test helpers."""

import io
import json
import sys
from unittest.mock import MagicMock, patch

from bexio.client import BexioClient


def mock_client(responses: list | dict) -> BexioClient:
    """Client whose _request returns items from responses in order."""
    if isinstance(responses, dict):
        responses = [responses]
    call_count = [0]

    def fake_request(method, path, params=None, body=None):
        result = responses[call_count[0] % len(responses)]
        call_count[0] += 1
        return result

    client = BexioClient("FAKE_TOKEN")
    client._request = fake_request
    return client


def capture(fn, args_list: list[str]) -> str:
    """Run fn(args, client, json_flag) via cli main with captured stdout."""
    from bexio.cli import main

    buf = io.StringIO()
    with patch("sys.argv", ["bexio"] + args_list), \
         patch("bexio.auth.get_token", return_value="FAKE_TOKEN"), \
         patch("sys.stdout", buf):
        try:
            main()
        except SystemExit:
            pass
    return buf.getvalue()


def capture_with_responses(argv: list[str], responses) -> str:
    """Run CLI with mocked client responses, return captured stdout."""
    if isinstance(responses, dict):
        responses = [responses]
    call_count = [0]

    def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
        result = responses[call_count[0] % len(responses)]
        call_count[0] += 1
        return result

    buf = io.StringIO()
    with patch("sys.argv", ["bexio"] + argv), \
         patch("bexio.auth.get_token", return_value="FAKE_TOKEN"), \
         patch("bexio.client.BexioClient._request", fake_request), \
         patch("sys.stdout", buf):
        try:
            from bexio.cli import main
            main()
        except SystemExit:
            pass
    return buf.getvalue()
