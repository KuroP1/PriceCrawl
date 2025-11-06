"""Shared crawler utilities and data structures."""
from __future__ import annotations

import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional


DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    ),
}


class RateLimiter:
    """Simple rate limiter that enforces a maximum number of calls per second."""

    def __init__(self, max_calls_per_second: float = 1.0) -> None:
        if max_calls_per_second <= 0:
            raise ValueError("max_calls_per_second must be positive")
        self._min_interval = 1.0 / max_calls_per_second
        self._lock = threading.Lock()
        self._last_called = 0.0

    def wait(self) -> None:
        """Block until another call is allowed."""

        with self._lock:
            now = time.monotonic()
            wait_time = self._min_interval - (now - self._last_called)
            if wait_time > 0:
                time.sleep(wait_time)
                now = time.monotonic()
            self._last_called = now


class HttpRequestException(Exception):
    """Raised when an HTTP request fails permanently."""

    def __init__(self, message: str, *, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class HttpResponse:
    status_code: int
    text: str
    headers: Dict[str, str]

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise HttpRequestException(f"HTTP {self.status_code}", status_code=self.status_code)


class HttpSession:
    """Very small HTTP session abstraction built on urllib."""

    def __init__(self) -> None:
        self.headers: Dict[str, str] = {}

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, str]] = None,
        data: Optional[bytes | str] = None,
        timeout: float = 10.0,
    ) -> HttpResponse:
        method = method.upper()
        full_url = url
        if params:
            query_string = urllib.parse.urlencode(params)
            delimiter = "&" if urllib.parse.urlparse(url).query else "?"
            full_url = f"{url}{delimiter}{query_string}"

        if isinstance(data, str):
            payload = data.encode("utf-8")
        else:
            payload = data

        request_obj = urllib.request.Request(
            full_url,
            data=payload,
            method=method,
            headers=self.headers,
        )

        try:
            with urllib.request.urlopen(request_obj, timeout=timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
                return HttpResponse(
                    status_code=response.getcode(),
                    text=body,
                    headers=dict(response.headers),
                )
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            return HttpResponse(
                status_code=exc.code,
                text=body,
                headers=dict(exc.headers or {}),
            )
        except urllib.error.URLError as exc:  # pragma: no cover - network failures
            raise HttpRequestException(str(exc)) from exc


def apply_default_headers(session: HttpSession) -> None:
    """Ensure anti-bot headers are always present on outgoing requests."""

    for key, value in DEFAULT_HEADERS.items():
        session.headers.setdefault(key, value)


def request_with_retry(
    session: HttpSession,
    method: str,
    url: str,
    *,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    rate_limiter: Optional[RateLimiter] = None,
    **kwargs,
) -> HttpResponse:
    """Perform an HTTP request with retries and exponential backoff."""

    if rate_limiter is None:
        rate_limiter = RateLimiter()

    for attempt in range(max_retries + 1):
        rate_limiter.wait()
        try:
            response = session.request(method, url, **kwargs)
            return response
        except HttpRequestException:
            if attempt >= max_retries:
                raise
            sleep_for = backoff_factor * (2 ** attempt)
            time.sleep(sleep_for)
    raise RuntimeError("Unreachable - retry loop should have returned or raised")


@dataclass
class PriceQuote:
    retailer: str
    name: str
    price: Decimal
    currency: str
    url: str


def normalize_price(raw_price: str) -> Decimal:
    """Normalize a price string into a Decimal value."""

    if not raw_price:
        raise ValueError("Price string is empty")

    cleaned = re.sub(r"[^0-9.,]", "", raw_price)
    if not cleaned:
        raise ValueError(f"Could not parse price from '{raw_price}'")

    # Replace thousand separators.
    cleaned = cleaned.replace(",", "")

    if cleaned.count(".") > 1:
        # Keep only the first decimal point.
        parts = cleaned.split(".")
        cleaned = parts[0] + "." + "".join(parts[1:])

    if "." not in cleaned:
        cleaned = f"{cleaned}.00"

    return Decimal(cleaned)


class BaseCrawler:
    """Shared functionality for HTTP powered crawlers."""

    search_url: str = ""
    retailer: str = ""
    rate_limiter: RateLimiter
    default_timeout: float = 10.0

    def __init__(
        self,
        session: Optional[HttpSession] = None,
        *,
        timeout: Optional[float] = None,
    ) -> None:
        self.session = session or HttpSession()
        apply_default_headers(self.session)
        self.rate_limiter = RateLimiter(max_calls_per_second=1.0)
        if timeout is None:
            timeout = self.default_timeout
        self.request_timeout = timeout

    def get(self, url: str, **kwargs) -> HttpResponse:
        timeout = kwargs.pop("timeout", self.request_timeout)
        response = request_with_retry(
            self.session,
            "GET",
            url,
            rate_limiter=self.rate_limiter,
            timeout=timeout,
            **kwargs,
        )
        return response

    def _fetch_search_page(self, query: str) -> str:
        if not self.search_url:
            raise NotImplementedError("search_url must be defined in subclasses")
        try:
            response = self.get(self.search_url, params=self.build_query_params(query))
            response.raise_for_status()
        except HttpRequestException as exc:
            if getattr(exc, "status_code", None) == 404:
                # Some retailers return HTTP 404 when a query has no matches.
                # Treat this as an empty result set instead of a hard error.
                return ""
            raise
        return response.text

    def build_query_params(self, query: str) -> Dict[str, str]:
        return {"q": query}

    def fetch_prices(self, query: str) -> List[PriceQuote]:
        raise NotImplementedError
