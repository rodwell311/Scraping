"""Dual fetcher: curl_cffi (fast, TLS-impersonating) with Playwright fallback."""

from __future__ import annotations

from dataclasses import dataclass

from curl_cffi import requests as cffi_requests

DEFAULT_TIMEOUT = 30
DEFAULT_IMPERSONATE = "chrome124"
# Heuristic: pages this small are almost certainly a JS shell or a block page.
MIN_HTML_LEN = 800


@dataclass
class FetchResult:
    url: str
    html: str
    status: int
    engine: str  # "curl_cffi" | "playwright"


def fetch(
    url: str,
    *,
    render: bool = False,
    timeout: int = DEFAULT_TIMEOUT,
    impersonate: str = DEFAULT_IMPERSONATE,
    headers: dict[str, str] | None = None,
) -> FetchResult:
    """Fetch a URL. Falls back to Playwright when curl_cffi fails or returns a JS shell.

    render=True skips curl_cffi and goes straight to the browser.
    """
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"url must be http(s): {url!r}")

    if render:
        return _fetch_playwright(url, timeout=timeout)

    try:
        resp = cffi_requests.get(
            url,
            impersonate=impersonate,
            timeout=timeout,
            headers=headers,
            allow_redirects=True,
        )
        html = resp.text or ""
        if resp.status_code < 400 and len(html) >= MIN_HTML_LEN:
            return FetchResult(url, html, resp.status_code, "curl_cffi")
        fast = FetchResult(url, html, resp.status_code, "curl_cffi")
    except Exception:
        fast = None

    try:
        return _fetch_playwright(url, timeout=timeout)
    except Exception:
        if fast is None:
            raise
        return fast  # browser unavailable; return whatever curl_cffi got


def _fetch_playwright(url: str, *, timeout: int = DEFAULT_TIMEOUT) -> FetchResult:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
            )
            resp = page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
            return FetchResult(url, page.content(), resp.status if resp else 0, "playwright")
        finally:
            browser.close()
