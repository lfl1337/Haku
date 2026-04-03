import { useState } from "react";
import Layout from "./components/Layout";
import SingleMode from "./components/SingleMode";
import BatchMode from "./components/BatchMode";
import SearchMode from "./components/SearchMode";

export default function App() {
  const [mode, setMode] = useState("single");

  return (
    <Layout mode={mode} onModeChange={setMode}>
      {mode === "single" && <SingleMode />}
      {mode === "batch" && <BatchMode />}
      {mode === "search" && <SearchMode />}
    </Layout>
  );
}
