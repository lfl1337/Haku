import { open } from "@tauri-apps/plugin-dialog";

export default function FolderPicker({ label, value, onChange }) {
  const handlePick = async () => {
    const selected = await open({ directory: true, multiple: false });
    if (selected) {
      onChange(selected);
    }
  };

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
