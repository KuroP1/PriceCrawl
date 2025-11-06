# PriceCrawl

PriceCrawl is a two-part application that helps you find the best consumer electronics prices in Hong Kong.

- **Backend** – A FastAPI service that aggregates prices from local retailers using dedicated crawlers.
- **Frontend** – A Vite/React single-page app that lets you type a product keyword and view the aggregated offers.

## Getting started

### Backend API

1. Create and activate a Python virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install the backend dependencies:

   ```bash
   pip install -r backend/requirements.txt
   ```

3. Start the FastAPI server:

   ```bash
   uvicorn backend.app:app --reload
   ```

   The backend will automatically load crawlers for Broadway, Fortress, and Price.com.hk. When you send a `POST /search` request with a JSON body like `{ "query": "iphone" }`, the service collects results from each retailer, deduplicates them by product, and returns the lowest observed price for every SKU it finds.

### Frontend

1. Install dependencies and start the Vite development server:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. Open the provided local URL (typically `http://127.0.0.1:5173`) in your browser. Submit a product keyword and the app will call the backend to display the best prices it can find.

### Tests

- Run the Python unit tests:

  ```bash
  pytest backend/tests
  ```

- Run the frontend tests:

  ```bash
  cd frontend
  npm run test
  ```

## Notes

- The crawlers perform live HTTP requests to the retailers' public search pages. Be mindful of network connectivity and rate limits when issuing many queries in a short period.
- If you want to extend support to additional stores, create a crawler that produces `PriceQuote` objects and register it via an adapter in `backend/services/adapters.py`.
