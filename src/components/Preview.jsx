export default function Preview({ original, processed }) {
  if (!original && !processed) {
    return (
      <div className="preview preview--empty">
        <p className="preview__placeholder">Kein Bild ausgewählt</p>
      </div>
    );
  }

  return (
    <div className="preview">
      <div className="preview__panel">
        <span className="preview__label">Vorher</span>
        {original ? (
          <img
            className="preview__img"
            src={`data:image/png;base64,${original}`}
            alt="Original"
          />
        ) : (
          <div className="preview__placeholder-box" />
        )}
      </div>
      <div className="preview__arrow">→</div>
      <div className="preview__panel">
        <span className="preview__label">Nachher</span>
        {processed ? (
          <img
            className="preview__img"
            src={`data:image/png;base64,${processed}`}
            alt="Processed"
          />
        ) : (
          <div className="preview__placeholder-box" />
        )}
      </div>
    </div>
  );
}
