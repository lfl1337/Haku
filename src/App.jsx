import { useState } from "react";

export default function App() {
  const [mode, setMode] = useState("single");

  return (
    <div style={{ padding: 24, color: '#e8e8f0' }}>
      <h1>Haku 白</h1>
      <p>Mode: {mode}</p>
      <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
        <button onClick={() => setMode("single")}>Einzel</button>
        <button onClick={() => setMode("batch")}>Batch</button>
        <button onClick={() => setMode("search")}>Suche</button>
      </div>
    </div>
  );
}
