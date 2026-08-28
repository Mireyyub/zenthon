import { ChatPanel } from "./components/ChatPanel";
import { StatusPanel } from "./components/StatusPanel";

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo">L</span>
          <div>
            <strong>Leon</strong>
            <span className="sub">UI · Phase 9 · yalnız /api/v1</span>
          </div>
        </div>
        <div className="topbar-meta">
          <span className="pill">no AI in browser</span>
          <span className="pill">127.0.0.1</span>
        </div>
      </header>

      <main className="layout">
        <ChatPanel />
        <StatusPanel />
      </main>

      <footer className="footer">
        Backend: FastAPI · ReasoningEngine server-side · Tauri shell hələ yoxdur
      </footer>
    </div>
  );
}
