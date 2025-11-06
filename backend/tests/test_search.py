from typing import List
from unittest.mock import Mock

from backend.services.search import SearchService


class FakeAdapter:
    def __init__(self, name: str, results: List[dict]):
        self.name = name
        self._results = results

    def search(self, query: str):  # pragma: no cover - simple stub
        return list(self._results)


def test_deduplicates_by_sku_and_keeps_lowest_price():
    adapter_a = FakeAdapter(
        "RetailerA",
        [
            {"sku": "123", "name": "Widget", "price": 10.0, "currency": "usd"},
            {"sku": "456", "name": "Gadget", "price": 15.0},
        ],
    )
    adapter_b = FakeAdapter(
        "RetailerB",
        [
            {"sku": "123", "name": "Widget", "price": 9.5, "currency": "USD"},
            {"sku": "789", "name": "Doohickey", "price": 12.0},
        ],
    )

    service = SearchService(adapters=[adapter_a, adapter_b])
    payload = service.search("widget")

    assert payload["errors"] == []
    assert len(payload["results"]) == 3

    widget_entry = next(item for item in payload["results"] if item["sku"] == "123")
    assert widget_entry["price"] == 9.5
    assert widget_entry["currency"] == "USD"


def test_results_are_sorted_by_price():
    adapter = FakeAdapter(
        "Retailer",
        [
            {"sku": "A", "name": "Item A", "price": 25},
            {"sku": "B", "name": "Item B", "price": 5},
            {"sku": "C", "name": "Item C", "price": 15},
        ],
    )

    service = SearchService(adapters=[adapter])
    payload = service.search("item")

    prices = [item["price"] for item in payload["results"]]
    assert prices == sorted(prices)


def test_adapter_errors_are_captured_and_other_results_returned():
    working_adapter = FakeAdapter(
        "GoodRetailer",
        [{"sku": "X", "name": "Item X", "price": 1.99}],
    )
    failing_adapter = Mock()
    failing_adapter.name = "BadRetailer"
    failing_adapter.search.side_effect = RuntimeError("boom")

    service = SearchService(adapters=[working_adapter, failing_adapter])
    payload = service.search("item")

    assert payload["results"] == [
        {
            "sku": "X",
            "name": "Item X",
            "retailer": "GoodRetailer",
            "price": 1.99,
            "currency": "USD",
            "url": None,
        }
    ]
    assert payload["errors"] == [{"adapter": "BadRetailer", "error": "boom"}]
