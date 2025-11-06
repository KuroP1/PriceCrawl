"""Crawler implementation for Broadway."""
from __future__ import annotations

from typing import List, Optional
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

from ..base import BaseCrawler, PriceQuote, normalize_price


class BroadwayCrawler(BaseCrawler):
    retailer = "Broadway"
    search_url = "https://www.broadwaylifestyle.com/search"

    def fetch_prices(self, query: str) -> List[PriceQuote]:
        html = self._fetch_search_page(query)
        if not html.strip():
            return []
        return self._parse(html)

    def _parse(self, html: str) -> List[PriceQuote]:
        root = _get_root(html)
        quotes: List[PriceQuote] = []

        for product in root.iter("li"):
            if not _has_class(product, "product-card"):
                continue

            title_el = _find_by_class(product, "span", "product-card__title")
            price_el = _find_by_class(product, "span", "product-card__price")
            link_el = _find_link(product)

            if title_el is None or price_el is None or link_el is None:
                continue

            name = "".join(title_el.itertext()).strip()
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


def fetch_prices(query: str) -> List[PriceQuote]:
    """Convenience wrapper for module-level usage."""

    return BroadwayCrawler().fetch_prices(query)


__all__ = ["BroadwayCrawler", "fetch_prices"]
