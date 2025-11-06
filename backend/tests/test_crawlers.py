from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import pytest

from backend.crawlers.price_crawler.broadway import (
    BroadwayCrawler,
    fetch_prices as fetch_broadway_prices,
)
from backend.crawlers.price_crawler.fortress import (
    FortressCrawler,
    fetch_prices as fetch_fortress_prices,
)
from backend.crawlers.price_crawler.price_dot_com import (
    PriceDotComCrawler,
    fetch_prices as fetch_price_dot_com_prices,
)

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def assert_quotes_match(quotes, expected):
    assert len(quotes) == len(expected)
    for quote, exp in zip(quotes, expected):
        assert quote.retailer == exp["retailer"]
        assert quote.name == exp["name"]
        assert quote.price == Decimal(exp["price"])
        assert quote.currency == exp["currency"]
        assert quote.url == exp["url"]


def test_fortress_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    html = load_fixture("fortress_search.html")

    def fake_fetch(self, query: str) -> str:  # pragma: no cover - runtime patched
        return html

    monkeypatch.setattr(FortressCrawler, "_fetch_search_page", fake_fetch)

    expected = [
        {
            "retailer": "Fortress",
            "name": "Apple iPhone 15 Pro 256GB",
            "price": "9999.00",
            "currency": "HKD",
            "url": "https://www.fortress.com.hk/en/product/iphone-15-pro",
        },
        {
            "retailer": "Fortress",
            "name": "Dyson V15 Detect Absolute",
            "price": "6680.00",
            "currency": "HKD",
            "url": "https://www.fortress.com.hk/en/product/dyson-v15",
        },
    ]

    crawler = FortressCrawler()
    quotes = crawler.fetch_prices("iphone")
    assert_quotes_match(quotes, expected)

    wrapper_quotes = fetch_fortress_prices("iphone")
    assert_quotes_match(wrapper_quotes, expected)


def test_broadway_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    html = load_fixture("broadway_search.html")

    def fake_fetch(self, query: str) -> str:  # pragma: no cover - runtime patched
        return html

    monkeypatch.setattr(BroadwayCrawler, "_fetch_search_page", fake_fetch)

    expected = [
        {
            "retailer": "Broadway",
            "name": "Sony A7C Mirrorless Camera",
            "price": "12490.00",
            "currency": "HKD",
            "url": "https://www.broadwaylifestyle.com/product/sony-a7c",
        },
        {
            "retailer": "Broadway",
            "name": "Nintendo Switch OLED",
            "price": "2680.00",
            "currency": "HKD",
            "url": "https://www.broadwaylifestyle.com/product/nintendo-switch",
        },
    ]

    crawler = BroadwayCrawler()
    quotes = crawler.fetch_prices("sony")
    assert_quotes_match(quotes, expected)

    wrapper_quotes = fetch_broadway_prices("sony")
    assert_quotes_match(wrapper_quotes, expected)


def test_price_dot_com_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    html = load_fixture("price_dot_com_search.html")

    def fake_fetch(self, query: str) -> str:  # pragma: no cover - runtime patched
        return html

    monkeypatch.setattr(PriceDotComCrawler, "_fetch_search_page", fake_fetch)

    expected = [
        {
            "retailer": "Price.com.hk",
            "name": "Apple iPhone 15 Pro 256GB",
            "price": "9299.00",
            "currency": "HKD",
            "url": "http://www.price.com.hk/product/apple-iphone-15-pro-256gb",
        },
        {
            "retailer": "Price.com.hk",
            "name": "Sony WH-1000XM5 Headphones",
            "price": "2999.00",
            "currency": "HKD",
            "url": "http://www.price.com.hk/product/sony-wh-1000xm5",
        },
    ]

    crawler = PriceDotComCrawler()
    quotes = crawler.fetch_prices("iphone")
    assert_quotes_match(quotes, expected)

    wrapper_quotes = fetch_price_dot_com_prices("iphone")
    assert_quotes_match(wrapper_quotes, expected)
