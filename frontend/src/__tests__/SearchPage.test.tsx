import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SearchPage from '../SearchPage';
import type { SearchResult } from '../types';

describe('SearchPage', () => {
  const renderSearchPage = () => render(<SearchPage />);

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('submits the search form and displays results', async () => {
    const mockResults: SearchResult[] = [
      {
        retailerName: 'Retailer A',
        price: 19.99,
        inStock: true,
        lastUpdated: '2024-01-01T12:00:00Z'
      }
    ];

    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockResults
    } as Response);

    renderSearchPage();

    const input = screen.getByLabelText(/product/i);
    await userEvent.type(input, 'headphones');

    const submitButton = screen.getByRole('button', { name: /search/i });
    await userEvent.click(submitButton);

    expect(fetchMock).toHaveBeenCalledWith('/search', expect.objectContaining({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: 'headphones' })
    }));

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /results/i })).toBeInTheDocument();
      expect(screen.getByText('Retailer A')).toBeInTheDocument();
      expect(screen.getByText(/\$19.99/)).toBeInTheDocument();
      expect(screen.getByText(/in stock/i)).toBeInTheDocument();
    });
  });

  it('shows a loading state while fetching', async () => {
    const fetchPromise = new Promise<Response>(() => {});
    vi.spyOn(globalThis, 'fetch').mockReturnValueOnce(fetchPromise);

    renderSearchPage();

    const input = screen.getByLabelText(/product/i);
    await userEvent.type(input, 'monitor');

    const form = screen.getByRole('form', { name: /product search/i });
    fireEvent.submit(form);

    expect(screen.getByRole('status')).toHaveTextContent(/loading results/i);
  });

  it('renders an error message when the request fails', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 500
    } as Response);

    renderSearchPage();

    const input = screen.getByLabelText(/product/i);
    await userEvent.type(input, 'webcam');
    const submitButton = screen.getByRole('button', { name: /search/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText(/unable to fetch prices/i)).toBeInTheDocument();
    });
  });
});
