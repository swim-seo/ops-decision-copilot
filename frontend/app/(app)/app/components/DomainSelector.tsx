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
  onComplete: (collectionName: string, domainContext: string, domainName: string) => void;
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
      onComplete(data.collection_name, data.domain_context ?? name, name);
    } catch (e) {
      alert("설정 실패: " + e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="mb-8">
        <div className="inline-flex items-center gap-2 border border-signal/30 bg-signal/5 px-2.5 py-1 font-ui text-[11px] font-medium tracking-[0.02em] text-signal">
          <span className="h-1.5 w-1.5 bg-signal" />
          1단계 · 도메인
        </div>
        <h1 className="mt-4 font-display text-[30px] font-medium leading-tight tracking-tight text-balance break-keep text-ink">어떤 데이터인가요?</h1>
        <p className="mt-2 max-w-[42ch] break-keep text-[14px] text-ink2">
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
          className="w-full border border-rule bg-sheet px-4 py-3.5 text-sm text-ink placeholder-ink3 outline-none transition focus:border-signal focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-watch"
        />
        {domain && (
          <button
            onClick={() => setDomain("")}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-ink3 transition hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-watch"
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
            className={`border px-3 py-1.5 text-xs transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-watch ${
              domain === s.label
                ? "border-signal/40 bg-signal/10 text-signal"
                : "border-rule bg-sheet text-ink2 hover:border-ink3 hover:text-ink"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      <button
        onClick={handleConfirm}
        disabled={loading}
        className="mt-8 flex w-full items-center justify-center gap-2 bg-ink py-3 text-sm font-semibold text-paper transition hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-watch disabled:cursor-not-allowed disabled:opacity-50"
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

      <p className="mt-3 text-center text-xs text-ink3">
        비워두면 범용으로 분석합니다
      </p>
    </div>
  );
}
