"""
Canva Connect API client.

Handles:
- OAuth 2.0 Authorization Code + PKCE flow
- Creating designs from templates
- Auto-filling text elements
- Exporting designs as PNG images
- Token refresh

Docs: https://www.canva.dev/docs/connect/
"""

import base64
import hashlib
import json
import logging
import os
import secrets
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

import requests

import config

logger = logging.getLogger(__name__)


# ─── OAuth PKCE Helpers ───────────────────────────────────────────────────────


def _generate_pkce() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) for PKCE."""
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


# ─── Local callback server ────────────────────────────────────────────────────


class _CallbackHandler(BaseHTTPRequestHandler):
    """Minimal HTTP server to capture the OAuth redirect."""
    code: str | None = None
    error: str | None = None

    def do_GET(self):  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            _CallbackHandler.code = params["code"][0]
            body = b"<h2>Authorisation successful! You can close this tab.</h2>"
        else:
            _CallbackHandler.error = params.get("error", ["unknown"])[0]
            body = b"<h2>Authorisation failed. Check the terminal.</h2>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # Suppress request logs


def _run_callback_server(port: int = 8080) -> str:
    """Start a local HTTP server, wait for the OAuth code, return it."""
    _CallbackHandler.code = None
    _CallbackHandler.error = None
    server = HTTPServer(("localhost", port), _CallbackHandler)
    server.timeout = 120  # Wait up to 2 minutes

    while _CallbackHandler.code is None and _CallbackHandler.error is None:
        server.handle_request()

    server.server_close()

    if _CallbackHandler.error:
        raise RuntimeError(f"OAuth error: {_CallbackHandler.error}")
    return _CallbackHandler.code


# ─── Token persistence ────────────────────────────────────────────────────────


def _save_tokens(access_token: str, refresh_token: str) -> None:
    """Persist tokens to .env so they survive restarts."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        env_path.touch()

    content = env_path.read_text()
    for key, value in [
        ("CANVA_ACCESS_TOKEN", access_token),
        ("CANVA_REFRESH_TOKEN", refresh_token),
    ]:
        if f"{key}=" in content:
            lines = content.splitlines()
            content = "\n".join(
                f"{key}={value}" if line.startswith(f"{key}=") else line
                for line in lines
            )
        else:
            content += f"\n{key}={value}"

    env_path.write_text(content)
    logger.info("Canva tokens saved to .env")


# ─── Main Canva Client ────────────────────────────────────────────────────────


class CanvaClient:
    """Wraps the Canva Connect REST API."""

    BASE = config.CANVA_API_BASE

    def __init__(self) -> None:
        self._access_token: str = config.CANVA_ACCESS_TOKEN
        self._refresh_token: str = config.CANVA_REFRESH_TOKEN

    # ── Auth ─────────────────────────────────────────────────────────────────

    def run_oauth_flow(self) -> None:
        """
        Interactive one-time OAuth setup.
        Opens the browser, captures the callback, saves tokens to .env.
        Run via: python main.py canva-auth
        """
        code_verifier, code_challenge = _generate_pkce()
        state = secrets.token_urlsafe(16)

        params = {
            "client_id": config.CANVA_CLIENT_ID,
            "redirect_uri": config.CANVA_REDIRECT_URI,
            "response_type": "code",
            "scope": "design:content:write design:content:read asset:read asset:write",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        auth_url = f"{config.CANVA_AUTH_URL}?{urllib.parse.urlencode(params)}"

        print(f"\nOpening browser for Canva authorisation...\n{auth_url}\n")
        webbrowser.open(auth_url)

        code = _run_callback_server(port=8080)

        # Exchange code for tokens
        resp = requests.post(
            config.CANVA_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": config.CANVA_REDIRECT_URI,
                "client_id": config.CANVA_CLIENT_ID,
                "client_secret": config.CANVA_CLIENT_SECRET,
                "code_verifier": code_verifier,
            },
            timeout=15,
        )
        resp.raise_for_status()
        tokens = resp.json()

        self._access_token = tokens["access_token"]
        self._refresh_token = tokens.get("refresh_token", "")
        _save_tokens(self._access_token, self._refresh_token)
        print("Canva OAuth complete. Tokens saved to .env")

    def _refresh_access_token(self) -> None:
        """Use the refresh token to get a new access token."""
        if not self._refresh_token:
            raise RuntimeError("No Canva refresh token. Run: python main.py canva-auth")

        resp = requests.post(
            config.CANVA_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
                "client_id": config.CANVA_CLIENT_ID,
                "client_secret": config.CANVA_CLIENT_SECRET,
            },
            timeout=15,
        )
        resp.raise_for_status()
        tokens = resp.json()
        self._access_token = tokens["access_token"]
        if "refresh_token" in tokens:
            self._refresh_token = tokens["refresh_token"]
        _save_tokens(self._access_token, self._refresh_token)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make an authenticated API request; auto-refresh token on 401."""
        url = f"{self.BASE}{path}"
        resp = requests.request(method, url, headers=self._headers(), **kwargs)

        if resp.status_code == 401:
            logger.info("Canva token expired, refreshing…")
            self._refresh_access_token()
            resp = requests.request(method, url, headers=self._headers(), **kwargs)

        resp.raise_for_status()
        return resp.json() if resp.content else {}

    # ── Design operations ─────────────────────────────────────────────────────

    def list_designs(self, query: str = "") -> list[dict]:
        """List designs in the user's Canva account."""
        params = {"limit": 50}
        if query:
            params["query"] = query
        return self._request("GET", "/designs", params=params).get("items", [])

    def create_design_from_template(self, template_id: str) -> str:
        """Create a new design based on a template. Returns the new design ID."""
        body = {
            "asset_id": template_id,
            "design_type": {"type": "preset", "name": "InstagramPost"},
        }
        resp = self._request("POST", "/designs", json=body)
        return resp["design"]["id"]

    def autofill_design(self, design_id: str, fields: list[dict]) -> None:
        """
        Fill text/image elements in a design.
        `fields` is a list of {"name": "element_name", "type": "text", "text": "..."}
        See: https://www.canva.dev/docs/connect/api-reference/autofills/create-design-autofill-job/
        """
        body = {"data": fields}
        resp = self._request("POST", f"/designs/{design_id}/autofill", json=body)
        job_id = resp.get("job", {}).get("id")
        if job_id:
            self._wait_for_autofill_job(design_id, job_id)

    def _wait_for_autofill_job(self, design_id: str, job_id: str, timeout: int = 60) -> None:
        """Poll until the autofill job completes."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            resp = self._request("GET", f"/designs/{design_id}/autofill/{job_id}")
            status = resp.get("job", {}).get("status", "")
            if status == "success":
                return
            if status == "failed":
                raise RuntimeError(f"Canva autofill job failed: {resp}")
            time.sleep(2)
        raise TimeoutError("Canva autofill job timed out")

    def export_design_as_png(self, design_id: str, output_path: Path) -> Path:
        """
        Request a PNG export of the design and download it to `output_path`.
        Returns the path to the saved file.
        """
        # Create export job
        resp = self._request(
            "POST",
            "/exports",
            json={"design_id": design_id, "format": {"type": "png", "export_quality": "pro"}},
        )
        job_id = resp.get("job", {}).get("id")
        if not job_id:
            raise RuntimeError(f"Failed to create Canva export job: {resp}")

        # Poll for completion
        download_url = self._wait_for_export(job_id)

        # Download the file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img_resp = requests.get(download_url, timeout=30)
        img_resp.raise_for_status()
        output_path.write_bytes(img_resp.content)
        logger.info("Exported design %s → %s", design_id, output_path)
        return output_path

    def _wait_for_export(self, job_id: str, timeout: int = 120) -> str:
        """Poll export job until done. Returns download URL."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            resp = self._request("GET", f"/exports/{job_id}")
            job = resp.get("job", {})
            status = job.get("status", "")
            if status == "success":
                urls = job.get("urls", [])
                if urls:
                    return urls[0]
                raise RuntimeError("Canva export succeeded but no download URL returned")
            if status == "failed":
                raise RuntimeError(f"Canva export job failed: {resp}")
            time.sleep(3)
        raise TimeoutError("Canva export job timed out")
