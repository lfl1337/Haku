export default function BackendStatus({ attempt, maxRetries, error }) {
  if (error) {
    return (
      <div className="backend-status error">
        <span className="backend-status__icon">✕</span>
        <p>{error}</p>
        <p className="backend-status__hint">Starte die App neu oder prüfe die Logs.</p>
      </div>
    );
  }

  return (
    <div className="backend-status loading">
      <div className="spinner" />
      <p>Backend wird gestartet...</p>
      <p className="backend-status__hint">{attempt} / {maxRetries}</p>
    </div>
  );
}
