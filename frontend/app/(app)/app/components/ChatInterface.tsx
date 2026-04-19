"use client";

import { useState, useRef, useEffect, FormEvent } from "react";

interface Message { role: "user" | "assistant"; content: string; }
interface Props { collectionName: string; domainContext: string; }

const SUGGESTIONS = ["재고 위험 항목이 있나요?", "이번 달 상위 제품은?", "공급업체 현황을 알려줘", "이상 징후가 있나요?"];

export default function ChatInterface({ collectionName, domainContext }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  async function send(text?: string) {
    const msg = (text ?? input).trim();
    if (!msg || streaming) return;
    setInput("");
    setMessages((p) => [...p, { role: "user", content: msg }, { role: "assistant", content: "" }]);
    setStreaming(true);
    try {
      const res = await fetch(`${BASE}/api/chat/message`, {
        method: "POST", headers: { "Content-Type": "application/json" },
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
            setMessages((p) => { const c = [...p]; c[c.length - 1] = { role: "assistant", content: c[c.length - 1].content + chunk }; return c; });
          }
        }
      }
    } catch (e) {
      setMessages((p) => { const c = [...p]; c[c.length - 1] = { role: "assistant", content: "오류가 발생했습니다: " + e }; return c; });
    } finally { setStreaming(false); inputRef.current?.focus(); }
  }

  return (
    <div className="flex h-full flex-col">
      {/* Messages */}
      <div className="flex-1 space-y-6 overflow-y-auto pr-1 pb-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-6 py-12">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/[0.04] text-2xl">
              <svg viewBox="0 0 20 20" fill="currentColor" className="h-6 w-6 text-slate-600">
                <path d="M3.505 2.365A41.369 41.369 0 019 2c1.863 0 3.601.124 5.495.365 1.247.167 2.18 1.108 2.435 2.268a4.45 4.45 0 00-.577-.069 43.141 43.141 0 00-4.706 0C9.229 4.696 7.5 6.727 7.5 8.998v2.24c0 1.413.67 2.735 1.76 3.562l-2.98 2.98A.75.75 0 015 17.25v-3.443c-.501-.048-1-.106-1.495-.172C2.033 13.438 1 12.162 1 10.72V5.28c0-1.441 1.033-2.717 2.505-2.914z"/>
              </svg>
            </div>
            <div className="text-center">
              <p className="font-medium text-slate-400">데이터에 대해 물어보세요</p>
              <p className="mt-1 text-xs text-slate-600">업로드된 파일을 기반으로 답변합니다</p>
            </div>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => send(s)} className="rounded-lg border border-white/[0.07] bg-white/[0.03] px-3 py-1.5 text-xs text-slate-500 transition hover:border-white/[0.12] hover:text-slate-300">
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={`flex items-start gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
              <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${m.role === "user" ? "bg-amber-500 text-slate-900" : "bg-white/[0.06] text-slate-400"}`}>
                {m.role === "user" ? "나" : "AI"}
              </div>
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${m.role === "user" ? "rounded-tr-sm bg-amber-500/10 text-amber-100 border border-amber-500/20" : "rounded-tl-sm bg-white/[0.04] text-slate-300 border border-white/[0.06]"}`}>
                <p className="whitespace-pre-wrap">{m.content}</p>
                {m.role === "assistant" && streaming && i === messages.length - 1 && (
                  <span className="ml-0.5 inline-block h-[14px] w-[2px] translate-y-[2px] animate-pulse bg-amber-400" />
                )}
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={(e: FormEvent) => { e.preventDefault(); send(); }} className="flex gap-2 border-t border-white/[0.06] pt-4">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="질문을 입력하세요..."
          disabled={streaming}
          className="flex-1 rounded-xl border border-white/[0.07] bg-white/[0.04] px-4 py-3 text-sm text-white placeholder-slate-600 outline-none transition focus:border-amber-500/40 focus:bg-white/[0.06] disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!input.trim() || streaming}
          className="flex items-center gap-1.5 rounded-xl bg-amber-500 px-5 py-3 text-sm font-semibold text-slate-900 transition hover:bg-amber-400 disabled:opacity-40"
        >
          <svg viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4">
            <path d="M2.87 2.298a.75.75 0 00-.812 1.021L3.39 6.624a1 1 0 00.928.626H8.25a.75.75 0 010 1.5H4.318a1 1 0 00-.927.626l-1.333 3.305a.75.75 0 00.811 1.022l11.5-4.25a.75.75 0 000-1.4l-11.5-4.25z"/>
          </svg>
        </button>
      </form>
    </div>
  );
}
