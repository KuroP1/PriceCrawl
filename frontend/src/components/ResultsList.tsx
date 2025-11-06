import type { SearchResult, SearchResponse } from '../types';

interface ResultsListProps {
  query: string;
  results: SearchResult[] | null;
  isLoading: boolean;
  error: string | null;
  adapterErrors: SearchResponse['errors'];
}

const ResultsList = ({ query, results, isLoading, error, adapterErrors }: ResultsListProps) => {
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

  const adapterErrorNotice =
    adapterErrors.length > 0 ? (
      <div role="status" className="adapter-errors">
        <p>We couldn&apos;t retrieve data from every retailer:</p>
        <ul>
          {adapterErrors.map(({ adapter, error: message }) => (
            <li key={adapter}>
              <strong>{adapter}:</strong> {message}
            </li>
          ))}
        </ul>
      </div>
    ) : null;

  if (!results || results.length === 0) {
    return (
      <div>
        {adapterErrorNotice}
        {query ? <p>No results found for “{query}”.</p> : <p>Search for a product to see prices.</p>}
      </div>
    );
  }

  return (
    <section aria-live="polite">
      <h2>Results</h2>
      {adapterErrorNotice}
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

