"use client";

import { useEffect, useState } from "react";

import Markdown from "./Markdown";

/**
 * 브리핑 4개 카드.
 *
 * 리스크는 히어로로 승격해 먼저 읽히게 하고, 나머지는 3열로 정렬한다.
 * 색은 의미 전용이다 — 빨강은 리스크, 파랑은 인사이트, 앰버는 다음 행동.
 * 요약은 상태가 없는 성격이라 중립색을 쓴다.
 */

interface Card { id: string; label: string; color: string; answer: string }
interface Props { collectionName: string; domainContext: string }

const HERO_ID = "risk";
const REST_ORDER = ["summary", "insight", "action"];

/** 카드 성격에 따른 의미색. 앰버(signal)는 '다음 행동'에만 쓴다. */
const ACCENT: Record<string, { stripe: string; mark: string; text: string }> = {
  risk:    { stripe: "bg-crit",   mark: "bg-crit",   text: "text-crit" },
  insight: { stripe: "bg-watch",  mark: "bg-watch",  text: "text-watch" },
  action:  { stripe: "bg-signal", mark: "bg-signal", text: "text-signal" },
  summary: { stripe: "bg-ink3",   mark: "bg-ink3",   text: "text-ink2" },
};

function accentOf(id: string) {
  return ACCENT[id] ?? ACCENT.summary;
}

export default function BriefingCards({ collectionName, domainContext }: Props) {
  const [cards, setCards] = useState<Card[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/briefing/generate`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ collection_name: collectionName, domain_context: domainContext }),
          }
        );
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        if (alive) setCards(data.cards ?? []);
      } catch (e) {
        if (alive) setError(String(e));
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [collectionName, domainContext]);

  if (loading) {
    return (
      <section className="border border-rule bg-sheet px-6 py-16">
        <p className="font-data text-[10px] tracking-[0.02em] text-ink3">분석 중</p>
        <p className="mt-3 max-w-[46ch] break-keep font-display text-[19px] leading-relaxed text-ink">
          업로드한 데이터를 읽고 오늘 확인할 것을 정리하고 있습니다.
        </p>
        <div className="mt-6 flex gap-1.5" aria-hidden="true">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="seq-lift h-[3px] w-10 bg-rule"
              style={{ "--d": `${i * 140}ms` } as React.CSSProperties}
            />
          ))}
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="border border-rule bg-sheet px-6 py-8">
        <p className="font-data text-[10px] tracking-[0.02em] text-crit">브리핑 실패</p>
        <p className="mt-2 break-keep text-[13px] text-ink">
          브리핑을 만들지 못했습니다. 파일이 적재됐는지 확인한 뒤 다시 시도하세요.
        </p>
        <p className="mt-3 max-w-[70ch] break-words font-data text-[11px] text-ink3">{error}</p>
      </section>
    );
  }

  const hero = cards.find((c) => c.id === HERO_ID);
  const rest = REST_ORDER
    .map((id) => cards.find((c) => c.id === id))
    .filter((c): c is Card => Boolean(c))
    .concat(cards.filter((c) => c.id !== HERO_ID && !REST_ORDER.includes(c.id)));

  if (!hero && rest.length === 0) {
    return (
      <section className="border border-rule bg-sheet px-6 py-8">
        <p className="font-data text-[10px] tracking-[0.02em] text-ink3">브리핑 없음</p>
        <p className="mt-2 text-[13px] text-ink">
          분석할 내용이 없습니다. 파일을 추가하면 브리핑이 다시 만들어집니다.
        </p>
      </section>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {hero && (
        <article className="relative border border-rule bg-sheet px-6 py-6 sm:pl-8">
          <span
            className={`absolute left-0 top-0 h-full w-[3px] ${accentOf(hero.id).stripe}`}
            aria-hidden="true"
          />
          <p className={`font-data text-[10px] tracking-[0.02em] ${accentOf(hero.id).text}`}>
            {hero.label} · 먼저 확인
          </p>
          <Markdown
            text={hero.answer}
            className="mt-3 max-w-[62ch] break-keep font-display text-[17px] leading-[1.75] text-ink"
          />
        </article>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        {rest.map((card, i) => {
          const accent = accentOf(card.id);
          return (
            <article
              key={card.id}
              className="seq-lift flex flex-col border border-rule bg-sheet px-5 py-5"
              style={{ "--d": `${120 + i * 70}ms` } as React.CSSProperties}
            >
              <div className="flex items-center gap-2">
                <span className={`h-2 w-2 ${accent.mark}`} aria-hidden="true" />
                <h3 className="font-data text-[10px] tracking-[0.02em] text-ink2">
                  {card.label}
                </h3>
              </div>
              <Markdown text={card.answer} className="mt-3 break-keep text-[13px] leading-relaxed text-ink" />
            </article>
          );
        })}
      </div>
    </div>
  );
}
