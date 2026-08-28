import { FormEvent, useRef, useState } from "react";
import { postChat } from "../api/client";
import type { ChatMessage } from "../api/types";

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "sys",
      role: "system",
      text: "Leon UI — yalnız /api/v1. AI məntiqi serverdədir.",
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    const userMsg: ChatMessage = { id: uid(), role: "user", text };
    setMessages((m) => [...m, userMsg]);
    setBusy(true);
    const res = await postChat(text);
    setBusy(false);
    if (res.error) {
      setMessages((m) => [
        ...m,
        {
          id: uid(),
          role: "assistant",
          text: `Xəta: ${res.error}`,
          meta: { error: res.error },
        },
      ]);
    } else {
      const d = res.data || {};
      const answer =
        d.answer ||
        (typeof d === "object" && "conclusion" in d
          ? String((d as { conclusion?: string }).conclusion)
          : "") ||
        "(boş cavab)";
      setMessages((m) => [
        ...m,
        {
          id: uid(),
          role: "assistant",
          text: answer,
          meta: d,
        },
      ]);
    }
    queueMicrotask(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }));
  }

  return (
    <section className="panel chat-panel">
      <header className="panel-header">
        <h2>Chat</h2>
        <span className="hint">POST /api/v1/chat</span>
      </header>
      <div className="messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`bubble ${msg.role}`}>
            <div className="bubble-text">{msg.text}</div>
            {msg.role === "assistant" && msg.meta && (
              <div className="bubble-meta">
                {msg.meta.confidence != null && (
                  <span>conf {Number(msg.meta.confidence).toFixed(2)}</span>
                )}
                {msg.meta.source && <span>src {msg.meta.source}</span>}
                {msg.meta.trace_id && <span>trace {msg.meta.trace_id}</span>}
                {msg.meta.llm_used != null && (
                  <span>llm {msg.meta.llm_used ? "yes" : "no"}</span>
                )}
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <form className="composer" onSubmit={onSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Leon-a yaz…"
          disabled={busy}
          autoComplete="off"
        />
        <button type="submit" disabled={busy || !input.trim()}>
          {busy ? "…" : "Göndər"}
        </button>
      </form>
    </section>
  );
}
