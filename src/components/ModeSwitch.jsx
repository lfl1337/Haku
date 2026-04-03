const modes = [
  { key: "single", label: "Einzel" },
  { key: "batch", label: "Batch" },
  { key: "search", label: "Suche" },
];

export default function ModeSwitch({ mode, onModeChange }) {
  return (
    <div className="mode-switch">
      {modes.map((m) => (
        <button
          key={m.key}
          className={`mode-switch__btn ${mode === m.key ? "mode-switch__btn--active" : ""}`}
          onClick={() => onModeChange(m.key)}
        >
          {m.label}
        </button>
      ))}
    </div>
  );
}
