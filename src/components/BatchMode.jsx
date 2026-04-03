import { useState } from "react";
import FolderPicker from "./FolderPicker";
import ProgressBar from "./ProgressBar";
import ImageGrid from "./ImageGrid";
import { useProcess } from "../hooks/useProcess";

export default function BatchMode() {
  const [inputDir, setInputDir] = useState("");
  const [outputDir, setOutputDir] = useState("");
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [previews, setPreviews] = useState([]);
  const [status, setStatus] = useState("idle");
  const { processBatch, loading, error } = useProcess();

  const handleBatch = async () => {
    if (!inputDir || !outputDir) return;
    setPreviews([]);
    setProgress({ current: 0, total: 0 });
    setStatus("processing");

    await processBatch(inputDir, outputDir, (event) => {
      if (event.status === "processing") {
        setProgress({ current: event.progress, total: event.total });
      } else if (event.status === "done") {
        setPreviews((prev) => [
          ...prev,
          { src: `data:image/png;base64,${event.preview}`, title: event.file },
        ]);
      } else if (event.status === "complete") {
        setStatus("complete");
      } else if (event.status === "error") {
        setPreviews((prev) => [
          ...prev,
          { src: null, title: `❌ ${event.file}` },
        ]);
      }
    });
  };

  return (
    <div className="batch-mode">
      <div className="batch-mode__controls">
        <div className="batch-mode__folders">
          <FolderPicker label="Eingabe" value={inputDir} onChange={setInputDir} />
          <FolderPicker label="Ausgabe" value={outputDir} onChange={setOutputDir} />
        </div>

        <button
          className="btn btn--primary"
          onClick={handleBatch}
          disabled={!inputDir || !outputDir || loading}
        >
          {loading ? "Verarbeite..." : "▶ Batch verarbeiten"}
        </button>
      </div>

      {error && <p className="error-msg">{error}</p>}

      {(loading || status === "complete") && (
        <ProgressBar
          current={progress.current}
          total={progress.total}
          label={status === "complete" ? "Fertig!" : "Verarbeite..."}
        />
      )}

      {previews.length > 0 && (
        <ImageGrid images={previews} />
      )}

      {status === "complete" && (
        <p className="success-msg">
          Alle Bilder verarbeitet — Ausgabe in <code>{outputDir}</code>
        </p>
      )}
    </div>
  );
}
