"""Crawler implementation for Price.com.hk."""
from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Dict, List, Optional
from urllib.parse import urljoin

from ..base import BaseCrawler, PriceQuote, normalize_price


class PriceDotComCrawler(BaseCrawler):
    retailer = "Price.com.hk"
    search_url = "https://www.price.com.hk/search.php"

    def build_query_params(self, query: str) -> Dict[str, str]:
        return {"g": "0", "q": query}

    def fetch_prices(self, query: str) -> List[PriceQuote]:
        html = self._fetch_search_page(query)
        if not html.strip():
            return []
        return self._parse(html)

    def _parse(self, html: str) -> List[PriceQuote]:
        parser = _ProductTileParser()
        parser.feed(html)
        parser.close()

        quotes: List[PriceQuote] = []
        for tile in parser.tiles:
            try:
                price = normalize_price(tile.price)
            except ValueError:
                continue

            quotes.append(
                PriceQuote(
                    retailer=self.retailer,
                    name=tile.name,
                    price=price,
                    currency="HKD",
                    url=urljoin("https://www.price.com.hk", tile.url or ""),
                )
            )

        return quotes


@dataclass
class _Tile:
    name: str
    price: str
    url: Optional[str]


@dataclass
class _TileAccumulator:
    name_parts: List[str]
    price_parts: List[str]
    url: Optional[str]
    depth: int = 1


class _ProductTileParser(HTMLParser):
    """Extract product tiles from Price.com.hk result pages."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tiles: List[_Tile] = []
        self._current: Optional[_TileAccumulator] = None
        self._stack: List[Dict[str, object]] = []
        self._title_depth = 0
        self._price_depth = 0
        self._capture_name = 0
        self._capture_price = 0

    def handle_starttag(self, tag: str, attrs):  # type: ignore[override]
        attr_dict = dict(attrs)
        classes = attr_dict.get("class", "").split()
        node = {"tag": tag, "classes": classes}
        self._stack.append(node)

        if tag == "div" and "product-list-item" in classes:
            if self._current is None:
                self._current = _TileAccumulator(name_parts=[], price_parts=[], url=None)
            else:
                self._current.depth += 1
            return

        if self._current is None:
            return

        if tag == "div" and "product-list-item__title" in classes:
            self._title_depth += 1
        if tag == "div" and "product-list-item__price" in classes:
            self._price_depth += 1

        if tag == "a" and self._title_depth > 0 and "href" in attr_dict:
            self._capture_name += 1
            if not self._current.url:
                self._current.url = attr_dict["href"]

        if (
            tag == "span"
            and self._price_depth > 0
            and "product-price__value" in classes
        ):
            self._capture_price += 1

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if not self._stack:
            return

        node = self._stack.pop()
        classes = node.get("classes", [])

        if self._current is None:
            return

        if tag == "a" and self._capture_name > 0:
            self._capture_name -= 1
        if tag == "span" and self._capture_price > 0:
            self._capture_price -= 1

        if tag == "div":
            if "product-list-item__title" in classes and self._title_depth > 0:
                self._title_depth -= 1
            if "product-list-item__price" in classes and self._price_depth > 0:
                self._price_depth -= 1
            if "product-list-item" in classes:
                self._current.depth -= 1
                if self._current.depth <= 0:
                    name = "".join(self._current.name_parts).strip()
                    price = "".join(self._current.price_parts).strip()
                    url = self._current.url
                    if name and price:
                        self.tiles.append(_Tile(name=name, price=price, url=url))
                    self._current = None
                else:
                    # Nested tiles should continue capturing until the outer closes.
                    pass

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if not self._current:
            return

        if self._capture_name > 0:
            self._current.name_parts.append(data)
        if self._capture_price > 0:
            self._current.price_parts.append(data)


def fetch_prices(query: str) -> List[PriceQuote]:
    """Convenience wrapper for module-level usage."""

    return PriceDotComCrawler().fetch_prices(query)


__all__ = ["PriceDotComCrawler", "fetch_prices"]
