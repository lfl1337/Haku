import { useState } from "react";
import ImageGrid from "./ImageGrid";
import { useSearch } from "../hooks/useSearch";

export default function SearchMode({ onSelectForProcessing }) {
  const [query, setQuery] = useState("");
  const { searchImages, results, loading: searching, error: searchError } = useSearch();

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    await searchImages(query.trim());
  };

  const handleImageClick = (index) => {
    const img = results[index];
    if (onSelectForProcessing) {
      onSelectForProcessing({
        url: img.url,
        title: img.title,
        thumbnail: img.thumbnail,
      });
    }
  };

  return (
    <div className="search-mode">
      <form className="search-mode__bar" onSubmit={handleSearch}>
        <input
          className="search-mode__input"
          type="text"
          placeholder="Suchbegriff eingeben..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button
          className="btn btn--primary"
          type="submit"
          disabled={searching || !query.trim()}
        >
          {searching ? "Suche..." : "Suchen"}
        </button>
      </form>

      {searchError && <p className="error-msg">{searchError}</p>}

      {results.length > 0 && (
        <>
          <p className="search-mode__hint">Klicke ein Bild an um es zu verarbeiten</p>
          <ImageGrid
            images={results}
            onToggle={handleImageClick}
          />
        </>
      )}
    </div>
  );
}
