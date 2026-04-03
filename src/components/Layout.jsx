import ModeSwitch from "./ModeSwitch";

export default function Layout({ mode, onModeChange, children }) {
  return (
    <div className="layout">
      <header className="layout__header">
        <h1 className="layout__title">Haku <span className="layout__kanji">白</span></h1>
        <ModeSwitch mode={mode} onModeChange={onModeChange} />
      </header>
      <main className="layout__content">{children}</main>
    </div>
  );
}
