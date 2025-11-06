import type { SearchResult } from '../types';

interface ResultsListProps {
  query: string;
  results: SearchResult[] | null;
  isLoading: boolean;
  error: string | null;
}

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
          <li key={`${result.retailer}-${result.sku}`}>
            <h3>{result.name}</h3>
            <p>
              <strong>Retailer:</strong> {result.retailer}
            </p>
            <p>
              <strong>Price:</strong> {result.currency} {result.price.toFixed(2)}
            </p>
            <p>
              <strong>SKU:</strong> {result.sku}
            </p>
            {result.url && (
              <p>
                <a href={result.url} target="_blank" rel="noopener noreferrer">
                  View Product
                </a>
              </p>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
};

export default ResultsList;

