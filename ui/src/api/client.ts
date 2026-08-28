/**
 * Leon API client — ONLY talks to /api/v1.
 * No AI logic, no tools, no FS. Backend owns reasoning.
 */

import type {
  AgentsList,
  ChatResponse,
  DesktopStatus,
  HealthReport,
  ModelsStatus,
} from "./types";

const BASE =
  (import.meta as ImportMeta & { env?: { VITE_LEON_API?: string } }).env
    ?.VITE_LEON_API || "";

async function request<T>(
  path: string,
  init?: RequestInit
): Promise<{ data?: T; error?: string; status: number }> {
  try {
    const res = await fetch(`${BASE}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers || {}),
      },
    });
    const text = await res.text();
    let body: unknown = null;
    try {
      body = text ? JSON.parse(text) : null;
    } catch {
      body = { raw: text };
    }
    if (!res.ok) {
      const detail =
        typeof body === "object" && body && "detail" in body
          ? String((body as { detail: unknown }).detail)
          : text || res.statusText;
      return { error: detail, status: res.status };
    }
    return { data: body as T, status: res.status };
  } catch (e) {
    return {
      error: e instanceof Error ? e.message : String(e),
      status: 0,
    };
  }
}

export async function getHealth() {
  return request<HealthReport>("/api/v1/health");
}

export async function getDesktop() {
  return request<DesktopStatus>("/api/v1/system/desktop");
}

export async function getModels() {
  return request<ModelsStatus>("/api/v1/models");
}

export async function getAgents() {
  return request<AgentsList>("/api/v1/agents");
}

export async function postChat(message: string, opts?: { mode?: string; goal?: string }) {
  return request<ChatResponse>("/api/v1/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      mode: opts?.mode || "auto",
      goal: opts?.goal || null,
    }),
  });
}

export async function postReason(query: string) {
  return request<ChatResponse>("/api/v1/reason", {
    method: "POST",
    body: JSON.stringify({ query, strategy: "auto", use_brain: true }),
  });
}
