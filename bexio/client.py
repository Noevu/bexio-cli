"""Bexio REST API client (stdlib only, no requests)."""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

BASE_URL = "https://api.bexio.com/2.0"


class BexioClient:
    def __init__(self, token: str) -> None:
        self._token = token

    def get(self, path: str, params: dict | None = None) -> Any:
        return self._request("GET", path, params=params)

    def get_v3(self, path: str, params: dict | None = None) -> Any:
        return self._request("GET", path, params=params, base="https://api.bexio.com/3.0")

    def post(self, path: str, body: dict | None = None) -> Any:
        return self._request("POST", path, body=body)

    def put(self, path: str, body: dict | None = None) -> Any:
        return self._request("PUT", path, body=body)

    def delete(self, path: str) -> Any:
        return self._request("DELETE", path)

    def _request(self, method: str, path: str, params: dict | None = None, body: dict | None = None, base: str | None = None) -> Any:
        url = (base or BASE_URL) + path
        if params:
            url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")
            sys.exit(f"HTTP {e.code} {e.reason}: {msg}")
