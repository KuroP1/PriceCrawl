import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SearchPage from '../SearchPage';
import type { SearchResponse } from '../types';

describe('SearchPage', () => {
  const renderSearchPage = () => render(<SearchPage />);

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('submits the search form and displays results', async () => {
    const mockResponse: SearchResponse = {
      results: [
        {
          sku: 'sku-1',
          name: 'Noise Cancelling Headphones',
          retailer: 'Retailer A',
          price: 1999,
          currency: 'HKD',
          url: 'https://example.com/product'
        }
      ],
      errors: []
    };

    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
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
      expect(screen.getByText('Noise Cancelling Headphones')).toBeInTheDocument();
      expect(screen.getByText(/Retailer:\s+Retailer A/)).toBeInTheDocument();
      expect(screen.getByText(/Price:\s+HKD 1999.00/)).toBeInTheDocument();
      expect(screen.getByText(/SKU:/)).toHaveTextContent('SKU: sku-1');
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

  it('surfaces adapter-specific errors from the backend response', async () => {
    const mockResponse: SearchResponse = {
      results: [],
      errors: [
        {
          adapter: 'Price.com.hk',
          error: 'HTTP 403'
        }
      ]
    };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    } as Response);

    renderSearchPage();

    const input = screen.getByLabelText(/product/i);
    await userEvent.type(input, 'camera');
    const submitButton = screen.getByRole('button', { name: /search/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/No results found/)).toBeInTheDocument();
      expect(screen.getByText(/Price\.com.hk/)).toBeInTheDocument();
      expect(screen.getByText(/HTTP 403/)).toBeInTheDocument();
    });
  });
});
