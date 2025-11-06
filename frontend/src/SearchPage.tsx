import { useState } from 'react';
import SearchForm from './components/SearchForm';
import ResultsList from './components/ResultsList';
import type { SearchResult, SearchResponse } from './types';

const SearchPage = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [adapterErrors, setAdapterErrors] = useState<SearchResponse['errors']>([]);

  const handleSearch = async (searchQuery: string) => {
    setQuery(searchQuery);
    setLoading(true);
    setError(null);
    setAdapterErrors([]);

    try {
      const response = await fetch('/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: searchQuery })
      });

      if (!response.ok) {
        throw new Error(`Search failed with status ${response.status}`);
      }

      const data: SearchResponse = await response.json();
      setResults(data.results || []);
      setAdapterErrors(data.errors || []);
    } catch (err) {
      setResults(null);
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      setAdapterErrors([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <header>
        <h1>Price Crawl</h1>
      </header>
      <main>
        <SearchForm onSearch={handleSearch} isLoading={loading} />
        <ResultsList
          query={query}
          results={results}
          isLoading={loading}
          error={error}
          adapterErrors={adapterErrors}
        />
      </main>
    </div>
  );
};

export default SearchPage;
