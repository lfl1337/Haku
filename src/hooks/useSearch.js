import { useState } from "react";

const API = "http://127.0.0.1:23431";

export function useSearch() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);

  const searchImages = async (query, maxResults = 20) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ q: query, max_results: maxResults });
      const res = await fetch(`${API}/search/images?${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResults(data.results);
      return data.results;
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return { searchImages, results, loading, error };
}
