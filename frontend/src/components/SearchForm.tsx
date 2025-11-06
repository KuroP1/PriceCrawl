import { FormEvent, useState } from 'react';

interface SearchFormProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
}

const SearchForm = ({ onSearch, isLoading }: SearchFormProps) => {
  const [inputValue, setInputValue] = useState('');

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!inputValue.trim()) {
      return;
    }

    onSearch(inputValue.trim());
  };

  return (
    <form onSubmit={handleSubmit} aria-label="product search">
      <label htmlFor="search-query">Product</label>
      <input
        id="search-query"
        type="text"
        value={inputValue}
        onChange={(event) => setInputValue(event.target.value)}
        placeholder="Search for a product"
        disabled={isLoading}
      />
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Searching…' : 'Search'}
      </button>
    </form>
  );
};

export default SearchForm;
