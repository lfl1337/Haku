import { useState } from "react";
import Layout from "./components/Layout";
import SingleMode from "./components/SingleMode";
import BatchMode from "./components/BatchMode";
import SearchMode from "./components/SearchMode";
import BackendStatus from "./components/BackendStatus";
import { useBackendHealth } from "./hooks/useBackendHealth";

export default function App() {
  const { ready, error, attempt, maxRetries } = useBackendHealth();
  const [mode, setMode] = useState("single");
  const [selectedSearchImage, setSelectedSearchImage] = useState(null);

  if (!ready) {
    return <BackendStatus attempt={attempt} maxRetries={maxRetries} error={error} />;
  }

  const handleSearchSelect = (image) => {
    setSelectedSearchImage(image);
    setMode("single");
  };

  return (
    <Layout mode={mode} onModeChange={setMode}>
      {mode === "single" && (
        <SingleMode
          searchImage={selectedSearchImage}
          onSearchImageConsumed={() => setSelectedSearchImage(null)}
        />
      )}
      {mode === "batch" && <BatchMode />}
      {mode === "search" && <SearchMode onSelectForProcessing={handleSearchSelect} />}
    </Layout>
  );
}
