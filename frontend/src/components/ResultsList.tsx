import type { SearchResult } from '../types';

interface ResultsListProps {
  query: string;
  results: SearchResult[] | null;
  isLoading: boolean;
  error: string | null;
}

const formatTimestamp = (timestamp: string) => {
  const date = new Date(timestamp);
  return Number.isNaN(date.getTime()) ? timestamp : date.toLocaleString();
};

const ResultsList = ({ query, results, isLoading, error }: ResultsListProps) => {
  if (isLoading) {
    return <p role="status">Loading results…</p>;
  }

  if (error) {
    return (
      <div role="alert">
        <p>Unable to fetch prices right now.</p>
        <pre>{error}</pre>
      </div>
    );
  }

  if (!results || results.length === 0) {
    return query ? <p>No results found for “{query}”.</p> : <p>Search for a product to see prices.</p>;
  }

  return (
    <section aria-live="polite">
      <h2>Results</h2>
      <ul>
        {results.map((result) => (
          <li key={`${result.retailerName}-${result.lastUpdated}`}>
            <h3>{result.retailerName}</h3>
            <p>
              <strong>Price:</strong> ${result.price.toFixed(2)}
            </p>
            <p>
              <strong>Status:</strong> {result.inStock ? 'In stock' : 'Out of stock'}
            </p>
            <p>
              <strong>Last updated:</strong> {formatTimestamp(result.lastUpdated)}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
};

export default ResultsList;
