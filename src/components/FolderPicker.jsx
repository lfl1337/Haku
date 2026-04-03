import { useState, useEffect } from "react";

let tauriDialog = null;

// Detect Tauri environment and lazy-load dialog
const isTauri = typeof window !== "undefined" && window.__TAURI_INTERNALS__;
if (isTauri) {
  import("@tauri-apps/plugin-dialog").then((mod) => {
    tauriDialog = mod;
  });
}

export default function FolderPicker({ label, value, onChange }) {
  const [editing, setEditing] = useState(false);
  const [inputValue, setInputValue] = useState(value || "");

  useEffect(() => {
    setInputValue(value || "");
  }, [value]);

  const handlePick = async () => {
    if (isTauri && tauriDialog) {
      const selected = await tauriDialog.open({ directory: true, multiple: false });
      if (selected) {
        onChange(selected);
      }
    } else {
      setEditing(true);
    }
  };

  const handleInputConfirm = () => {
    setEditing(false);
    if (inputValue.trim()) {
      onChange(inputValue.trim());
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleInputConfirm();
    if (e.key === "Escape") setEditing(false);
  };

  return (
    <div className="folder-picker">
      <span className="folder-picker__label">{label}</span>
      {editing ? (
        <input
          className="folder-picker__input"
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onBlur={handleInputConfirm}
          onKeyDown={handleKeyDown}
          placeholder="z.B. F:\Output"
          autoFocus
        />
      ) : (
        <button className="folder-picker__btn" onClick={handlePick}>
          <span className="folder-picker__icon">📂</span>
          <span className="folder-picker__path">
            {value || "Ordner wählen..."}
          </span>
        </button>
      )}
    </div>
  );
}
