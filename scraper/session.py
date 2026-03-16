"""Login + session management with anti-blocking delays."""

from __future__ import annotations

import asyncio
import logging
import random
import urllib.parse

import httpx
from bs4 import BeautifulSoup

from config.settings import settings
from scraper.endpoints import BASE_EIP, LOGIN_ACTION, LOGIN_PAGE, ROOT_URL

logger = logging.getLogger(__name__)


class SessionExpired(Exception):
    pass


class LoginFailed(Exception):
    pass


class VGHSession:
    """Manages authenticated httpx session to VGHTPE EMR."""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._csrf_token: str | None = None
        self._logged_in = False

    # ── lifecycle ──────────────────────────────────────────────

    async def start(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
            },
        )

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._logged_in = False

    # ── auth ───────────────────────────────────────────────────

    async def login(
        self,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        username = username or settings.vgh_username
        password = password or settings.vgh_password
        if not username or not password:
            raise LoginFailed("VGH_USERNAME / VGH_PASSWORD not set")

        assert self._client is not None

        # 1. GET login page → CSRF token
        resp = await self._client.get(LOGIN_PAGE)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        meta = soup.find("meta", {"name": "csrf-token"})
        self._csrf_token = meta["content"] if meta else None

        # 2. POST login
        data = {
            "login_name": username,
            "password": password,
            "loginCheck": "1",
            "fromAjax": "1",
        }
        headers = {
            "X-CSRF-TOKEN": self._csrf_token or "",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": LOGIN_PAGE,
        }
        resp = await self._client.post(LOGIN_ACTION, data=data, headers=headers)
        resp.raise_for_status()
        result = resp.json()

        error_code = int(result.get("error", -1))
        if error_code != 0:
            raise LoginFailed(f"Login returned error code {error_code}")

        # 3. Follow redirect chain (same as senior's code)
        if "url" in result:
            dash = await self._client.get(BASE_EIP + "/" + result["url"])
            redirect_path = dash.text.split("/")[1][:-2]
            await self._client.get(BASE_EIP + "/" + redirect_path)

        self._logged_in = True
        logger.info("VGH login successful")

    # ── request helpers ────────────────────────────────────────

    async def _ensure_login(self) -> None:
        if not self._logged_in:
            await self.login()

    async def get(self, url: str, *, retries: int = 3) -> str:
        """GET with anti-blocking delay, retry, and auto-relogin."""
        await self._ensure_login()
        assert self._client is not None

        delay = random.uniform(settings.request_delay_min, settings.request_delay_max)
        await asyncio.sleep(delay)

        for attempt in range(1, retries + 1):
            try:
                resp = await self._client.get(url)
                if resp.status_code in (429, 503):
                    wait = 60 * (2 ** (attempt - 1))  # 60s, 120s, 240s
                    logger.warning("Rate limited (%s), waiting %ss", resp.status_code, wait)
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp.text
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 401:
                    logger.info("Session expired, re-logging in")
                    self._logged_in = False
                    await self.login()
                    continue
                if attempt == retries:
                    raise
                await asyncio.sleep(5 * attempt)

        raise RuntimeError(f"Failed to GET {url} after {retries} retries")

    async def get_bytes(self, url: str) -> bytes:
        """GET binary content (images)."""
        await self._ensure_login()
        assert self._client is not None
        delay = random.uniform(settings.request_delay_min, settings.request_delay_max)
        await asyncio.sleep(delay)
        resp = await self._client.get(url)
        resp.raise_for_status()
        return resp.content
