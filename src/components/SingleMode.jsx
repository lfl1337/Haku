import { useState, useRef, useEffect } from "react";
import FolderPicker from "./FolderPicker";
import Preview from "./Preview";
import { useProcess } from "../hooks/useProcess";

export default function SingleMode({ searchImage, onSearchImageConsumed }) {
  const [outputDir, setOutputDir] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileName, setFileName] = useState("");
  const [imageUrl, setImageUrl] = useState(null);
  const [thumbnailSrc, setThumbnailSrc] = useState(null);
  const fileInputRef = useRef(null);
  const { processSingle, processFromUrl, loading, result, error } = useProcess();

  // When a search image arrives, set it up for processing
  useEffect(() => {
    if (searchImage) {
      setImageUrl(searchImage.url);
      setFileName(searchImage.title || "Suchbild");
      setThumbnailSrc(searchImage.thumbnail || searchImage.url);
      setSelectedFile(null);
      onSearchImageConsumed?.();
    }
  }, [searchImage]);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setFileName(file.name);
      setImageUrl(null);
      setThumbnailSrc(URL.createObjectURL(file));
    }
  };

  const handleProcess = async () => {
    if (!outputDir) return;

    if (imageUrl) {
      const safeName = fileName.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 50) || "image";
      await processFromUrl(imageUrl, outputDir, safeName);
    } else if (selectedFile) {
      await processSingle(selectedFile, outputDir);
    }
  };

  const hasInput = selectedFile || imageUrl;

  return (
    <div className="single-mode">
      <div className="single-mode__controls">
        <div className="single-mode__file-row">
          <div className="single-mode__file-picker">
            <span className="folder-picker__label">Bild</span>
            <button
              className="folder-picker__btn"
              onClick={() => fileInputRef.current?.click()}
            >
              <span className="folder-picker__icon">🖼️</span>
              <span className="folder-picker__path">
                {fileName || "Bild wählen..."}
              </span>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/webp,image/bmp"
              onChange={handleFileSelect}
              style={{ display: "none" }}
            />
          </div>
          <FolderPicker
            label="Ausgabe"
            value={outputDir}
            onChange={setOutputDir}
          />
        </div>

        <button
          className="btn btn--primary"
          onClick={handleProcess}
          disabled={!hasInput || !outputDir || loading}
        >
          {loading ? "Verarbeite..." : "▶ Verarbeiten"}
        </button>
      </div>

      {error && <p className="error-msg">{error}</p>}

      {thumbnailSrc && !result && (
        <div className="preview">
          <div className="preview__panel">
            <span className="preview__label">Vorschau</span>
            <img className="preview__img" src={thumbnailSrc} alt="Ausgewählt" />
          </div>
        </div>
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
