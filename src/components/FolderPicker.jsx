import { useState, useEffect } from "react";

let tauriDialog = null;

const isTauri = typeof window !== "undefined" && window.__TAURI_INTERNALS__;
if (isTauri) {
  import("@tauri-apps/plugin-dialog").then((mod) => {
    tauriDialog = mod;
  });
}

export default function FolderPicker({ label, value, onChange }) {
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
    }
  };

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
    onChange(e.target.value);
  };

  // In Tauri: native folder dialog button
  if (isTauri) {
    return (
      <div className="folder-picker">
        <span className="folder-picker__label">{label}</span>
        <button className="folder-picker__btn" onClick={handlePick}>
          <span className="folder-picker__icon">📂</span>
          <span className="folder-picker__path">
            {value || "Ordner wählen..."}
          </span>
        </button>
      </div>
    );
  }

  // In Browser: text input for path
  return (
    <div className="folder-picker">
      <span className="folder-picker__label">{label}</span>
      <input
        className="folder-picker__input"
        type="text"
        value={inputValue}
        onChange={handleInputChange}
        placeholder="Pfad eingeben, z.B. F:\Output"
      />
    </div>
  );
}
