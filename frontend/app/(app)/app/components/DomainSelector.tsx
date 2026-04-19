"use client";

import { useState } from "react";

const SUGGESTIONS = [
  { label: "뷰티 / 이커머스", icon: "✦" },
  { label: "공급망 / 재고", icon: "✦" },
  { label: "제조 / 생산", icon: "✦" },
  { label: "물류 / 배송", icon: "✦" },
  { label: "에너지", icon: "✦" },
  { label: "금융 / 회계", icon: "✦" },
];

interface Props {
  onComplete: (collectionName: string, domainContext: string) => void;
}

export default function DomainSelector({ onComplete }: Props) {
  const [domain, setDomain] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleConfirm() {
    const name = domain.trim() || "generic";
    setLoading(true);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/domain/setup`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name }),
        }
      );
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      onComplete(data.collection_name, data.domain_context ?? name);
    } catch (e) {
      alert("설정 실패: " + e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="mb-8">
        <div className="mb-1 inline-flex items-center gap-2 rounded-full border border-amber-500/20 bg-amber-500/5 px-3 py-1 text-xs font-medium text-amber-500">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
          Step 1 of 2
        </div>
        <h1 className="mt-4 text-3xl font-bold tracking-tight text-white">어떤 데이터인가요?</h1>
        <p className="mt-2 text-slate-500">
          업종이나 용도를 적어주세요. AI가 맥락을 파악해 더 정확하게 분석합니다.
        </p>
      </div>

      <div className="relative">
        <input
          type="text"
          placeholder="예: 뷰티 브랜드 재고 관리, 물류 배송 현황..."
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !loading && handleConfirm()}
          autoFocus
          className="w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3.5 text-white placeholder-slate-600 outline-none ring-0 transition focus:border-amber-500/50 focus:bg-white/[0.06] text-sm"
        />
        {domain && (
          <button
            onClick={() => setDomain("")}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-600 hover:text-slate-400"
          >
            <svg viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4">
              <path d="M5.28 4.22a.75.75 0 00-1.06 1.06L6.94 8l-2.72 2.72a.75.75 0 101.06 1.06L8 9.06l2.72 2.72a.75.75 0 101.06-1.06L9.06 8l2.72-2.72a.75.75 0 00-1.06-1.06L8 6.94 5.28 4.22z"/>
            </svg>
          </button>
        )}
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s.label}
            onClick={() => setDomain(s.label)}
            className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-all ${
              domain === s.label
                ? "border-amber-500/40 bg-amber-500/10 text-amber-400"
                : "border-white/[0.07] bg-white/[0.03] text-slate-500 hover:border-white/[0.12] hover:text-slate-300"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      <button
        onClick={handleConfirm}
        disabled={loading}
        className="mt-8 flex w-full items-center justify-center gap-2 rounded-xl bg-amber-500 py-3 text-sm font-semibold text-slate-900 transition hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? (
          <>
            <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z"/>
            </svg>
            설정 중...
          </>
        ) : (
          <>다음으로 <span className="opacity-60">→</span></>
        )}
      </button>

      <p className="mt-3 text-center text-xs text-slate-700">
        비워두면 범용으로 분석합니다
      </p>
    </div>
  );
}
