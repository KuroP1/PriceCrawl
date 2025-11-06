"""Adapters connecting crawlers to the :class:`SearchService`."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, List, MutableMapping, Optional
from urllib.parse import urlparse

from backend.crawlers.base import PriceQuote
from backend.crawlers.price_crawler.broadway import BroadwayCrawler
from backend.crawlers.price_crawler.fortress import FortressCrawler
from backend.crawlers.price_crawler.price_dot_com import PriceDotComCrawler


@dataclass
class PriceCrawlerAdapter:
    """Wrap a crawler implementation so it matches ``CrawlerAdapter``."""

    crawler: object
    name: str

    def search(self, query: str) -> Iterable[MutableMapping[str, object]]:
        quotes = _fetch_quotes(self.crawler, query)
        return [_quote_to_product_dict(quote) for quote in quotes]


def _fetch_quotes(crawler: object, query: str) -> List[PriceQuote]:
    fetch = getattr(crawler, "fetch_prices", None)
    if fetch is None:
        raise AttributeError("Crawler must define a 'fetch_prices' method")
    quotes = fetch(query)
    if not isinstance(quotes, list):
        quotes = list(quotes)
    return quotes


def _quote_to_product_dict(quote: PriceQuote) -> MutableMapping[str, object]:
    sku = _derive_sku(quote)
    price_value = _decimal_to_float(quote.price)
    return {
        "sku": sku,
        "name": quote.name,
        "retailer": quote.retailer,
        "price": price_value,
        "currency": quote.currency,
        "url": quote.url,
    }


def _derive_sku(quote: PriceQuote) -> str:
    """Generate a stable SKU surrogate from the product name and URL."""

    name_key = re.sub(r"\s+", " ", quote.name).strip().lower()
    url_key: Optional[str] = None
    if quote.url:
        parsed = urlparse(quote.url)
        path = parsed.path.rstrip("/")
        if path:
            url_key = path.split("/")[-1].lower()
    base = name_key if url_key is None else f"{name_key}|{url_key}"
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]
    return digest


def _decimal_to_float(value: Decimal) -> float:
    return float(value)


def build_default_adapters() -> List[PriceCrawlerAdapter]:
    """Return the default set of adapters for Hong Kong retailers."""

    return [
        PriceCrawlerAdapter(crawler=BroadwayCrawler(), name="Broadway"),
        PriceCrawlerAdapter(crawler=FortressCrawler(), name="Fortress"),
        PriceCrawlerAdapter(crawler=PriceDotComCrawler(), name="Price.com.hk"),
    ]


__all__ = [
    "PriceCrawlerAdapter",
    "build_default_adapters",
]
