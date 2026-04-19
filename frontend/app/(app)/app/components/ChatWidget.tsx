"use client";

import { useState, useRef, useEffect, FormEvent } from "react";

interface Message { role: "user" | "assistant"; content: string; }
interface Props { collectionName: string; domainContext: string; }

const SUGGESTIONS = ["재고 위험 항목이 있나요?", "이번 달 상위 제품은?", "이상 징후가 있나요?"];

export default function ChatWidget({ collectionName, domainContext }: Props) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  useEffect(() => {
    if (open) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [messages, open]);

  async function send(text?: string) {
    const msg = (text ?? input).trim();
    if (!msg || streaming) return;
    setInput("");
    setMessages((p) => [...p, { role: "user", content: msg }, { role: "assistant", content: "" }]);
    setStreaming(true);
    try {
      const res = await fetch(`${BASE}/api/chat/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, collection_name: collectionName, domain_context: domainContext, stream: true }),
      });
      if (!res.ok) throw new Error(await res.text());
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop() ?? "";
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const chunk = line.slice(6);
            if (chunk === "[DONE]") break;
            setMessages((p) => {
              const c = [...p];
              c[c.length - 1] = { role: "assistant", content: c[c.length - 1].content + chunk };
              return c;
            });
          }
        }
      }
    } catch (e) {
      setMessages((p) => { const c = [...p]; c[c.length - 1] = { role: "assistant", content: "오류: " + e }; return c; });
    } finally {
      setStreaming(false);
      inputRef.current?.focus();
    }
  }

  const unread = !open && messages.length > 0 && messages[messages.length - 1].role === "assistant";

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
      {/* Chat panel */}
      {open && (
        <div className="flex h-[520px] w-[360px] flex-col overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0d0d14] shadow-2xl shadow-black/60">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-white/[0.06] px-4 py-3">
            <div className="flex items-center gap-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-500/10">
                <svg viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4 text-amber-400">
                  <path d="M3.505 2.365A41.369 41.369 0 019 2c1.863 0 3.601.124 5.495.365 1.247.167 2.18 1.108 2.435 2.268a4.45 4.45 0 00-.577-.069 43.141 43.141 0 00-4.706 0C9.229 4.696 7.5 6.727 7.5 8.998v2.24c0 1.413.67 2.735 1.76 3.562l-2.98 2.98A.75.75 0 015 17.25v-3.443c-.501-.048-1-.106-1.495-.172C2.033 13.438 1 12.162 1 10.72V5.28c0-1.441 1.033-2.717 2.505-2.914z"/>
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold text-white">AI 어시스턴트</p>
                <div className="flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  <span className="text-[10px] text-slate-500">온라인</span>
                </div>
              </div>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="flex h-7 w-7 items-center justify-center rounded-lg text-slate-600 transition hover:bg-white/[0.06] hover:text-slate-300"
            >
              <svg viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4">
                <path d="M3.72 3.72a.75.75 0 011.06 0L8 6.94l3.22-3.22a.75.75 0 111.06 1.06L9.06 8l3.22 3.22a.75.75 0 11-1.06 1.06L8 9.06l-3.22 3.22a.75.75 0 01-1.06-1.06L6.94 8 3.72 4.78a.75.75 0 010-1.06z"/>
              </svg>
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 space-y-4 overflow-y-auto p-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center gap-4 pt-6 text-center">
                <p className="text-sm text-slate-500">데이터에 대해 무엇이든 물어보세요</p>
                <div className="flex flex-col gap-1.5 w-full">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => send(s)}
                      className="rounded-lg border border-white/[0.06] bg-white/[0.03] px-3 py-2 text-left text-xs text-slate-500 transition hover:border-white/[0.1] hover:text-slate-300"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((m, i) => (
                <div key={i} className={`flex items-end gap-2 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
                  <div className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${m.role === "user" ? "bg-amber-500 text-slate-900" : "bg-white/[0.06] text-slate-400"}`}>
                    {m.role === "user" ? "나" : "AI"}
                  </div>
                  <div className={`max-w-[82%] rounded-2xl px-3 py-2.5 text-xs leading-relaxed ${
                    m.role === "user"
                      ? "rounded-br-sm bg-amber-500/10 text-amber-100 border border-amber-500/20"
                      : "rounded-bl-sm bg-white/[0.05] text-slate-300 border border-white/[0.06]"
                  }`}>
                    <p className="whitespace-pre-wrap">{m.content}</p>
                    {m.role === "assistant" && streaming && i === messages.length - 1 && (
                      <span className="ml-0.5 inline-block h-3 w-[2px] translate-y-[1px] animate-pulse bg-amber-400" />
                    )}
                  </div>
                </div>
              ))
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <form
            onSubmit={(e: FormEvent) => { e.preventDefault(); send(); }}
            className="flex items-center gap-2 border-t border-white/[0.06] p-3"
          >
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="질문 입력..."
              disabled={streaming}
              className="flex-1 rounded-lg border border-white/[0.07] bg-white/[0.04] px-3 py-2 text-xs text-white placeholder-slate-600 outline-none transition focus:border-amber-500/40 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!input.trim() || streaming}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-amber-500 text-slate-900 transition hover:bg-amber-400 disabled:opacity-40"
            >
              <svg viewBox="0 0 16 16" fill="currentColor" className="h-3.5 w-3.5">
                <path d="M2.87 2.298a.75.75 0 00-.812 1.021L3.39 6.624a1 1 0 00.928.626H8.25a.75.75 0 010 1.5H4.318a1 1 0 00-.927.626l-1.333 3.305a.75.75 0 00.811 1.022l11.5-4.25a.75.75 0 000-1.4l-11.5-4.25z"/>
              </svg>
            </button>
          </form>
        </div>
      )}

      {/* FAB */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="group relative flex h-14 w-14 items-center justify-center rounded-full bg-amber-500 shadow-lg shadow-amber-500/20 transition hover:bg-amber-400 hover:shadow-amber-500/30 hover:scale-105"
      >
        {/* unread dot */}
        {unread && (
          <span className="absolute -right-0.5 -top-0.5 flex h-3.5 w-3.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
            <span className="relative inline-flex h-3.5 w-3.5 rounded-full bg-red-500" />
          </span>
        )}
        {open ? (
          <svg viewBox="0 0 20 20" fill="currentColor" className="h-6 w-6 text-slate-900">
            <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"/>
          </svg>
        ) : (
          <svg viewBox="0 0 20 20" fill="currentColor" className="h-6 w-6 text-slate-900">
            <path d="M3.505 2.365A41.369 41.369 0 019 2c1.863 0 3.601.124 5.495.365 1.247.167 2.18 1.108 2.435 2.268a4.45 4.45 0 00-.577-.069 43.141 43.141 0 00-4.706 0C9.229 4.696 7.5 6.727 7.5 8.998v2.24c0 1.413.67 2.735 1.76 3.562l-2.98 2.98A.75.75 0 015 17.25v-3.443c-.501-.048-1-.106-1.495-.172C2.033 13.438 1 12.162 1 10.72V5.28c0-1.441 1.033-2.717 2.505-2.914z"/>
          </svg>
        )}
      </button>
    </div>
  );
}
