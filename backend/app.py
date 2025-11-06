from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.services.adapters import build_default_adapters
from backend.services.search import SearchService


class SearchQuery(BaseModel):
    query: str = Field(..., description="Product name or SKU to search for")


app = FastAPI(title="Price Crawl API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def setup_service() -> None:
    adapters = build_default_adapters()
    app.state.search_service = SearchService(adapters=adapters)


@app.post("/search")
async def search_products(payload: SearchQuery):
    service: SearchService = getattr(app.state, "search_service", None)
    if service is None:
        # This should never happen because we initialize on startup, but just in case.
        raise HTTPException(status_code=500, detail="Search service not available")

    result = service.search(payload.query)
    return result
