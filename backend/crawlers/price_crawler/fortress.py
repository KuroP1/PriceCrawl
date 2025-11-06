"""Crawler implementation for Fortress."""
from __future__ import annotations

from typing import List, Optional
from urllib.parse import quote_plus, urljoin
import xml.etree.ElementTree as ET

from ..base import BaseCrawler, PriceQuote, normalize_price


class FortressCrawler(BaseCrawler):
    retailer = "Fortress"
    search_url = "https://www.fortress.com.hk/en/search"

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("timeout", 25.0)
        super().__init__(*args, **kwargs)
        self.session.headers.setdefault("Referer", "https://www.fortress.com.hk/en/")

    def fetch_prices(self, query: str) -> List[PriceQuote]:
        html = self._fetch_search_page(query)
        if not html.strip():
            return []
        return self._parse(html)

    def _fetch_search_page(self, query: str) -> str:
        referer = _build_referer(self.search_url, query)
        previous_referer = self.session.headers.get("Referer")
        self.session.headers["Referer"] = referer
        try:
            response = self.get(
                self.search_url,
                params=self.build_query_params(query),
                timeout=self.request_timeout,
            )
            response.raise_for_status()
            return response.text
        finally:
            if previous_referer is None:
                self.session.headers.pop("Referer", None)
            else:
                self.session.headers["Referer"] = previous_referer

    def _parse(self, html: str) -> List[PriceQuote]:
        root = _get_root(html)
        quotes: List[PriceQuote] = []

        for tile in root.iter("div"):
            if not _has_class(tile, "product-tile"):
                continue

            name_el = _find_by_class(tile, "div", "product-title")
            price_el = _find_by_class(tile, "div", "product-price")
            link_el = _find_link(tile)

            if name_el is None or price_el is None or link_el is None:
                continue

            name = "".join(name_el.itertext()).strip()
            price = normalize_price("".join(price_el.itertext()).strip())
            currency = price_el.attrib.get("data-currency", "HKD")
            url = urljoin(self.search_url, link_el.attrib.get("href", ""))

            quotes.append(
                PriceQuote(
                    retailer=self.retailer,
                    name=name,
                    price=price,
                    currency=currency,
                    url=url,
                )
            )

        return quotes


def _has_class(element: ET.Element, expected: str) -> bool:
    class_attr = element.attrib.get("class", "")
    return expected in class_attr.split()


def _find_by_class(parent: ET.Element, tag: str, class_name: str) -> Optional[ET.Element]:
    for child in parent.iter(tag):
        if _has_class(child, class_name):
            return child
    return None


def _find_link(parent: ET.Element) -> Optional[ET.Element]:
    for child in parent.iter("a"):
        if "href" in child.attrib:
            return child
    return None


def _get_root(html: str) -> ET.Element:
    cleaned = html.lstrip()
    if cleaned.upper().startswith("<!DOCTYPE"):
        _, _, cleaned = cleaned.partition(">")
        cleaned = cleaned.lstrip()
    return ET.fromstring(cleaned)


def _build_referer(search_url: str, query: str) -> str:
    return f"{search_url}?q={quote_plus(query)}"


def fetch_prices(query: str) -> List[PriceQuote]:
    """Convenience wrapper for module-level usage."""

    return FortressCrawler().fetch_prices(query)


__all__ = ["FortressCrawler", "fetch_prices"]
