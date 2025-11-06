from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.services.search import SearchService


class SearchQuery(BaseModel):
    query: str = Field(..., description="Product name or SKU to search for")


app = FastAPI(title="Price Crawl API", version="1.0.0")


@app.on_event("startup")
async def setup_service() -> None:
    # Lazily initialize the search service with any real crawler adapters.
    app.state.search_service = SearchService(adapters=[])


@app.post("/search")
async def search_products(payload: SearchQuery):
    service: SearchService = getattr(app.state, "search_service", None)
    if service is None:
        # This should never happen because we initialize on startup, but just in case.
        raise HTTPException(status_code=500, detail="Search service not available")

    result = service.search(payload.query)
    return result
