"use client";

import { useEffect, useState } from "react";

interface Card { id: string; label: string; color: string; answer: string; }
interface Props { collectionName: string; domainContext: string; }

const CARD_STYLE: Record<string, { border: string; glow: string; labelColor: string; icon: React.ReactNode }> = {
  summary: {
    border: "border-blue-500/20",
    glow: "from-blue-500/5",
    labelColor: "text-blue-400",
    icon: <svg viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4"><path fillRule="evenodd" d="M2.5 3.75A.75.75 0 013.25 3h9.5a.75.75 0 010 1.5h-9.5A.75.75 0 012.5 3.75zm0 4A.75.75 0 013.25 7h9.5a.75.75 0 010 1.5h-9.5A.75.75 0 012.5 7.75zm0 4a.75.75 0 01.75-.75h4.5a.75.75 0 010 1.5h-4.5a.75.75 0 01-.75-.75z" clipRule="evenodd"/></svg>,
  },
  risk: {
    border: "border-red-500/20",
    glow: "from-red-500/5",
    labelColor: "text-red-400",
    icon: <svg viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4"><path fillRule="evenodd" d="M6.701 2.25c.577-1 2.02-1 2.598 0l5.196 9a1.5 1.5 0 01-1.299 2.25H2.804A1.5 1.5 0 011.505 11.25l5.196-9zM8 5a.75.75 0 01.75.75v2.5a.75.75 0 01-1.5 0v-2.5A.75.75 0 018 5zm0 6a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd"/></svg>,
  },
  insight: {
    border: "border-emerald-500/20",
    glow: "from-emerald-500/5",
    labelColor: "text-emerald-400",
    icon: <svg viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4"><path d="M8 1.5A4.5 4.5 0 0012 6c0 1.13-.42 2.164-1.108 2.944A5 5 0 0112 12H4a5 5 0 011.108-3.056A4.5 4.5 0 014 6 4.5 4.5 0 018 1.5zM6.5 14.5v-1h3v1a.5.5 0 01-.5.5h-2a.5.5 0 01-.5-.5z"/></svg>,
  },
  action: {
    border: "border-amber-500/20",
    glow: "from-amber-500/5",
    labelColor: "text-amber-400",
    icon: <svg viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4"><path d="M5.52.359A.75.75 0 016.106 0h3.788a.75.75 0 01.74.871l-.83 4.875h3.045a.75.75 0 01.595 1.207l-6.25 8.25a.75.75 0 01-1.304-.65l1.175-5.893H3.25a.75.75 0 01-.596-1.207L5.52.359z"/></svg>,
  },
};

export default function BriefingCards({ collectionName, domainContext }: Props) {
  const [cards, setCards] = useState<Card[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/briefing/generate`,
          { method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ collection_name: collectionName, domain_context: domainContext }) }
        );
        if (!res.ok) throw new Error(await res.text());
        setCards((await res.json()).cards);
      } catch (e) { setError(String(e)); }
      finally { setLoading(false); }
    })();
  }, [collectionName, domainContext]);

  if (loading) return (
    <div className="flex flex-col items-center gap-3 py-24 text-slate-600">
      <svg className="h-6 w-6 animate-spin text-amber-500" viewBox="0 0 24 24" fill="none">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z"/>
      </svg>
      <p className="text-sm">AI가 데이터를 분석하는 중...</p>
    </div>
  );

  if (error) return <p className="py-10 text-center text-sm text-red-400/80">{error}</p>;

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-white">오늘의 브리핑</h2>
        <p className="text-sm text-slate-600">업로드된 데이터 기반 AI 분석 요약</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {cards.map((card) => {
          const style = CARD_STYLE[card.id] ?? { border: "border-white/10", glow: "from-white/5", labelColor: "text-slate-400", icon: null };
          return (
            <div key={card.id} className={`rounded-xl border bg-gradient-to-br ${style.border} ${style.glow} to-transparent p-5`}>
              <div className={`mb-3 flex items-center gap-2 ${style.labelColor}`}>
                {style.icon}
                <span className="text-xs font-semibold uppercase tracking-wider">{card.label}</span>
              </div>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-400">
                {card.answer}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
