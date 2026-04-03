import { useState } from "react";
import FolderPicker from "./FolderPicker";
import ImageGrid from "./ImageGrid";
import Preview from "./Preview";
import { useSearch } from "../hooks/useSearch";
import { useProcess } from "../hooks/useProcess";

export default function SearchMode() {
  const [query, setQuery] = useState("");
  const [outputDir, setOutputDir] = useState("");
  const [selected, setSelected] = useState([]);
  const { searchImages, results, loading: searching, error: searchError } = useSearch();
  const { processFromUrl, loading: processing, result, error: processError } = useProcess();

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSelected([]);
    await searchImages(query.trim());
  };

  const toggleSelect = (index) => {
    setSelected((prev) =>
      prev.includes(index)
        ? prev.filter((i) => i !== index)
        : [...prev, index]
    );
  };

  const handleProcessSelected = async () => {
    if (selected.length === 0 || !outputDir) return;
    for (const idx of selected) {
      const img = results[idx];
      const filename = img.title?.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 50) || `image_${idx}`;
      await processFromUrl(img.url, outputDir, filename);
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
      {processError && <p className="error-msg">{processError}</p>}

      {results.length > 0 && (
        <>
          <ImageGrid
            images={results}
            selected={selected}
            onToggle={toggleSelect}
          />

          <div className="search-mode__actions">
            <FolderPicker label="Ausgabe" value={outputDir} onChange={setOutputDir} />
            <div className="search-mode__action-row">
              <span className="search-mode__count">
                {selected.length} ausgewählt
              </span>
              <button
                className="btn btn--primary"
                onClick={handleProcessSelected}
                disabled={selected.length === 0 || !outputDir || processing}
              >
                {processing ? "Verarbeite..." : "▶ Auswahl verarbeiten"}
              </button>
            </div>
          </div>
        </>
      )}

      {result && (
        <Preview
          original={result.original_preview}
          processed={result.processed_preview}
        />
      )}

      {result?.success && (
        <p className="success-msg">
          Gespeichert: <code>{result.output_path}</code>
        </p>
      )}
    </div>
  );
}
