export interface SearchResult {
  sku: string;
  name: string;
  retailer: string;
  price: number;
  currency: string;
  url?: string | null;
}

export interface SearchResponse {
  results: SearchResult[];
  errors: Array<{
    adapter: string;
    error: string;
  }>;
}
