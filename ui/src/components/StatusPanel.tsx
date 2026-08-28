import { useCallback, useEffect, useState } from "react";
import { getAgents, getDesktop, getHealth, getModels } from "../api/client";
import type { AgentsList, DesktopStatus, HealthReport, ModelsStatus } from "../api/types";

export function StatusPanel() {
  const [health, setHealth] = useState<HealthReport | null>(null);
  const [desktop, setDesktop] = useState<DesktopStatus | null>(null);
  const [models, setModels] = useState<ModelsStatus | null>(null);
  const [agents, setAgents] = useState<AgentsList | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setErr(null);
    const [h, d, m, a] = await Promise.all([
      getHealth(),
      getDesktop(),
      getModels(),
      getAgents(),
    ]);
    if (h.error && d.error) {
      setErr(h.error || d.error || "API əlçatan deyil");
    }
    if (h.data) setHealth(h.data);
    if (d.data) setDesktop(d.data);
    if (m.data) setModels(m.data);
    if (a.data) setAgents(a.data);
    setLoading(false);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <section className="panel status-panel">
      <header className="panel-header">
        <h2>Status</h2>
        <button type="button" className="ghost" onClick={() => void refresh()} disabled={loading}>
          {loading ? "…" : "Yenilə"}
        </button>
      </header>

      {err && <div className="banner error">{err}</div>}

      <div className="cards">
        <div className="card">
          <h3>API / Health</h3>
          <p>
            <Badge ok={health?.ok !== false && !err} />{" "}
            {health?.ok === false ? "degraded" : err ? "offline" : "ok"}
          </p>
        </div>

        <div className="card">
          <h3>LLM</h3>
          <p>
            <Badge ok={!!models?.reachable} soft={!models?.reachable} />{" "}
            {models?.provider || "—"} / {models?.model || "—"}
          </p>
          <p className="muted">
            {models?.reachable ? "reachable" : "offline (soft — fallback işləyir)"}
          </p>
        </div>

        <div className="card">
          <h3>Desktop readiness</h3>
          <p>
            <Badge ok={!!desktop?.ready_for_tauri} /> ready_for_tauri:{" "}
            {String(desktop?.ready_for_tauri ?? "?")}
          </p>
          <p className="muted">
            production_desktop: {String(desktop?.ready_for_production_desktop ?? false)}
          </p>
          <p className="muted">
            UI today: {desktop?.ui_today || "—"} → {desktop?.ui_target || "—"}
          </p>
          <p className="muted">native: {desktop?.native_mode || "—"}</p>
        </div>

        <div className="card">
          <h3>Agents</h3>
          <p className="muted">
            prod: {(agents?.production || []).join(", ") || "react, coding"}
          </p>
          <p className="muted">all: {(agents?.agents || []).join(", ") || "—"}</p>
        </div>
      </div>

      {desktop?.notes && desktop.notes.length > 0 && (
        <ul className="notes">
          {desktop.notes.map((n, i) => (
            <li key={i}>{n}</li>
          ))}
        </ul>
      )}
    </section>
  );
}

function Badge({ ok, soft }: { ok: boolean; soft?: boolean }) {
  const cls = ok ? "badge ok" : soft ? "badge soft" : "badge bad";
  return <span className={cls}>{ok ? "●" : "○"}</span>;
}
