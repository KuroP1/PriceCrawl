"""Search service that orchestrates retailer crawler adapters."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, MutableMapping, Optional, Protocol, Sequence


class CrawlerAdapter(Protocol):
    """Protocol describing the public API of a crawler adapter."""

    name: str

    def search(self, query: str) -> Iterable[MutableMapping[str, Any]]:
        """Return an iterable of raw product dictionaries."""


@dataclass
class SearchResult:
    sku: str
    name: str
    retailer: str
    price: float
    currency: str
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SearchService:
    """Service responsible for aggregating search results from multiple adapters."""

    def __init__(self, adapters: Sequence[CrawlerAdapter]):
        self._adapters = list(adapters)

    def search(self, query: str) -> Dict[str, Any]:
        results: Dict[str, SearchResult] = {}
        errors: List[Dict[str, str]] = []

        for adapter in self._adapters:
            adapter_name = getattr(adapter, "name", adapter.__class__.__name__)
            try:
                for raw_product in adapter.search(query):
                    normalized = self._normalize_product(raw_product, adapter_name)
                    if normalized is None:
                        continue

                    existing = results.get(normalized.sku)
                    if existing is None or normalized.price < existing.price:
                        results[normalized.sku] = normalized
            except Exception as exc:  # pragma: no cover - defensive, validated via tests
                errors.append(
                    {
                        "adapter": adapter_name,
                        "error": str(exc),
                    }
                )

        sorted_results = sorted(results.values(), key=lambda item: item.price)
        return {
            "results": [item.to_dict() for item in sorted_results],
            "errors": errors,
        }

    @staticmethod
    def _normalize_product(raw: MutableMapping[str, Any], adapter_name: str) -> Optional[SearchResult]:
        sku = str(raw.get("sku") or raw.get("id") or "").strip()
        name = str(raw.get("name") or raw.get("title") or "").strip()
        retailer = str(raw.get("retailer") or adapter_name).strip()

        if not sku or not name:
            return None

        price = raw.get("price")
        try:
            price_value = float(price)
        except (TypeError, ValueError):
            return None

        currency = str(raw.get("currency") or "USD").strip().upper()
        url = raw.get("url")
        if url is not None:
            url = str(url)

        return SearchResult(
            sku=sku,
            name=name,
            retailer=retailer,
            price=price_value,
            currency=currency,
            url=url,
        )
