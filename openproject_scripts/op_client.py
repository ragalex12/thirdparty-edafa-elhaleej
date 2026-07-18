#!/usr/bin/env python3
"""Shared OpenProject REST API client for sync scripts."""
from __future__ import annotations

import os
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

DEFAULT_URL = "https://master.tailcf9988.ts.net:10081"

ENV_CANDIDATES = [
    Path("/opt/.env"),
    Path("/opt/odoo-log-report-2026-06-28/docs/.openproject.env"),
    Path("/opt/localaddons/openproject_tools/.openproject.env"),
]


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip("'\"")
        os.environ.setdefault(key, val)


def load_env() -> None:
    for path in ENV_CANDIDATES:
        load_dotenv(path)


def get_token() -> str:
    for key in ("OPENPROJECT_API_TOKEN", "OPENPROJECT_API_KEY"):
        if os.environ.get(key):
            return os.environ[key]
    return ""


def get_base_url() -> str:
    return os.environ.get("OPENPROJECT_URL", DEFAULT_URL).rstrip("/")


def get_project_id() -> int:
    return int(os.environ.get("OPENPROJECT_PROJECT_ID", "19"))


def get_parent_wp_id() -> int | None:
    raw = os.environ.get("OPENPROJECT_PARENT_WP_ID", "").strip()
    return int(raw) if raw else None


class OPClient:
    def __init__(self, base_url: str, token: str, dry_run: bool = False):
        self.base = base_url.rstrip("/")
        self.dry_run = dry_run
        self.auth = HTTPBasicAuth("apikey", token)
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}

    def _url(self, endpoint: str) -> str:
        return f"{self.base}/api/v3{endpoint}"

    def get(self, endpoint: str):
        try:
            return requests.get(self._url(endpoint), auth=self.auth, headers=self.headers, timeout=60)
        except requests.RequestException as e:
            print(f"[NET ERROR] GET {endpoint}: {e}")
            return None

    def post(self, endpoint: str, data: dict):
        if self.dry_run:
            print(f"[dry-run] POST {endpoint}")
            return None
        return requests.post(self._url(endpoint), json=data, auth=self.auth, headers=self.headers, timeout=60)

    def patch(self, endpoint: str, data: dict):
        if self.dry_run:
            print(f"[dry-run] PATCH {endpoint}")
            return None
        return requests.patch(self._url(endpoint), json=data, auth=self.auth, headers=self.headers, timeout=60)

    def connect(self, project_id: int | None = None) -> bool:
        pid = project_id if project_id is not None else get_project_id()
        r = self.get(f"/projects/{pid}")
        if r and r.status_code == 200:
            print(f"✓ Connected — project: {r.json().get('name')} (id={pid})")
            return True
        code = r.status_code if r else "unreachable"
        print(f"[ERROR] Cannot reach project {pid}: HTTP {code}")
        if r:
            print(r.text[:300])
        return False
