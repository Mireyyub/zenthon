/** Types for Leon /api/v1 responses — UI only, no reasoning. */

export type ChatResponse = {
  answer?: string;
  confidence?: number;
  confidence_label?: string;
  source?: string;
  trace_id?: string;
  llm_used?: boolean;
  reasoning_mode?: string;
  evidence?: unknown;
  decision?: unknown;
  session_id?: string | null;
  error?: string;
};

export type HealthReport = {
  ok?: boolean;
  components?: Record<string, unknown>;
};

export type DesktopStatus = {
  target?: string;
  cognitive_core?: string;
  api_ready?: boolean;
  llm_reachable?: boolean;
  llm_soft?: boolean;
  native_mode?: string;
  security_gate?: boolean;
  storage_sqlite?: boolean;
  ui_today?: string;
  ui_target?: string;
  shell_today?: string;
  shell_target?: string;
  offline_capable?: boolean;
  ready_for_tauri?: boolean;
  ready_for_production_desktop?: boolean;
  blockers?: string[];
  notes?: string[];
};

export type ModelsStatus = {
  provider?: string;
  reachable?: boolean;
  offline?: boolean;
  model?: string;
  models?: string[];
  error?: string | null;
};

export type AgentsList = {
  agents?: string[];
  production?: string[];
  experimental?: string[];
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  text: string;
  meta?: Partial<ChatResponse>;
};
