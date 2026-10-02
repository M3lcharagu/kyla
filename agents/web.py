"""A small, visible Playwright wrapper for deliberate browser tasks.

This module does not log in, bypass challenges, or run JavaScript supplied by a
caller. Use the headed CLI for human-supervised browsing. Headless mode is
available for local smoke tests and other explicitly non-interactive uses.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlsplit


class BrowserAgent:
    """Manage one Playwright browser, context, and page.

    Playwright is imported lazily so importing this module does not require the
    optional browser dependency. The default is headed Chromium.
    """

    _BROWSER_NAMES = ("chromium", "firefox", "webkit")

    def __init__(
        self,
        *,
        browser: str = "chromium",
        headless: bool = False,
        slow_mo_ms: int = 0,
        timeout_ms: int = 30_000,
    ) -> None:
        if browser not in self._BROWSER_NAMES:
            raise ValueError("browser must be chromium, firefox, or webkit")
        if isinstance(slow_mo_ms, bool) or not isinstance(slow_mo_ms, int) or slow_mo_ms < 0:
            raise ValueError("slow_mo_ms must be a non-negative integer")
        if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int) or timeout_ms <= 0:
            raise ValueError("timeout_ms must be a positive integer")

        self.browser_name = browser
        self.headless = headless
        self.slow_mo_ms = slow_mo_ms
        self.timeout_ms = timeout_ms
        self._playwright: Optional[Any] = None
        self._browser: Optional[Any] = None
        self._context: Optional[Any] = None
        self._page: Optional[Any] = None

    def start(self) -> "BrowserAgent":
        """Launch the selected browser and create a fresh page."""
        if self._page is not None:
            return self

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is not installed. Install it with "
                "'python -m pip install playwright' and then run "
                "'python -m playwright install chromium'."
            ) from exc

        self._playwright = sync_playwright().start()
        try:
            browser_type = getattr(self._playwright, self.browser_name)
            self._browser = browser_type.launch(
                headless=self.headless,
                slow_mo=self.slow_mo_ms,
            )
            self._context = self._browser.new_context()
            self._page = self._context.new_page()
            self._page.set_default_timeout(self.timeout_ms)
        except Exception:
            self.close()
            raise
        return self

    @property
    def page(self) -> Any:
        """Return the active Playwright page, or raise if not started."""
        if self._page is None:
            raise RuntimeError("BrowserAgent has not been started")
        return self._page

    @staticmethod
    def _validate_url(url: str) -> str:
        value = url.strip()
        parsed = urlsplit(value)
        if parsed.scheme == "about" and value == "about:blank":
            return value
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("Only absolute http(s) URLs and about:blank are allowed")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("Do not put credentials in a URL")
        return value

    def goto(self, url: str) -> Optional[Any]:
        """Navigate to an absolute HTTP(S) URL or about:blank."""
        safe_url = self._validate_url(url)
        return self.page.goto(
            safe_url,
            wait_until="domcontentloaded",
            timeout=self.timeout_ms,
        )

    def current_url(self) -> str:
        return self.page.url

    def title(self) -> str:
        return self.page.title()

    def text(self, selector: str = "body") -> str:
        """Return visible text for a CSS selector (defaults to the page body)."""
        return self.page.locator(selector).inner_text(timeout=self.timeout_ms)

    def click(self, selector: str) -> None:
        self.page.locator(selector).click(timeout=self.timeout_ms)

    def fill(self, selector: str, value: str) -> None:
        self.page.locator(selector).fill(value, timeout=self.timeout_ms)

    def screenshot(self, path: str, *, full_page: bool = True) -> Path:
        destination = Path(path).expanduser()
        self.page.screenshot(path=str(destination), full_page=full_page)
        return destination

    def set_content(self, html: str) -> None:
        """Set page markup directly; useful for local, network-free smoke tests."""
        self.page.set_content(html, wait_until="domcontentloaded", timeout=self.timeout_ms)

    def back(self) -> Optional[Any]:
        return self.page.go_back(wait_until="domcontentloaded", timeout=self.timeout_ms)

    def reload(self) -> Optional[Any]:
        return self.page.reload(wait_until="domcontentloaded", timeout=self.timeout_ms)

    def close(self) -> None:
        """Close browser resources. Safe to call more than once."""
        browser, playwright = self._browser, self._playwright
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        if playwright is not None:
            try:
                playwright.stop()
            except Exception:
                pass

    def __enter__(self) -> "BrowserAgent":
        return self.start()

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()
