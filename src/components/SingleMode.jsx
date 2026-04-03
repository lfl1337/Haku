import { useState, useRef } from "react";
import FolderPicker from "./FolderPicker";
import Preview from "./Preview";
import { useProcess } from "../hooks/useProcess";

export default function SingleMode() {
  const [outputDir, setOutputDir] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileName, setFileName] = useState("");
  const fileInputRef = useRef(null);
  const { processSingle, loading, result, error } = useProcess();

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setFileName(file.name);
    }
  };

  const handleProcess = async () => {
    if (!selectedFile || !outputDir) return;
    await processSingle(selectedFile, outputDir);
  };

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
          disabled={!selectedFile || !outputDir || loading}
        >
          {loading ? "Verarbeite..." : "▶ Verarbeiten"}
        </button>
      </div>

      {error && <p className="error-msg">{error}</p>}

      <Preview
        original={result?.original_preview}
        processed={result?.processed_preview}
      />

      {result?.success && (
        <p className="success-msg">
          Gespeichert: <code>{result.output_path}</code>
        </p>
      )}
    </div>
  );
}
