"use client";

import { useEffect, useMemo, useState } from "react";

/**
 * 사양 블록 + 참조 허브.
 *
 * 브리핑이 "어떤 테이블에서 나온 답인지"를 먼저 보여주는 출처 표시다.
 * 허브는 참조받은 횟수로 정렬한다 — 순서가 곧 정보(이 스키마의 축이 무엇인지)이고,
 * 아무것도 참조하지 않고 참조받지도 않는 테이블은 고립으로 따로 표시한다.
 */

interface GraphNode { id: string; type?: string }
interface GraphEdge { source: string; target: string; relation?: string }
interface Props {
  collectionName: string;
  domainContext: string;
  onSelectTable?: (tableId: string) => void;
}

interface Hub {
  id: string;
  count: number;
  referrers: string[];
}

const MAX_REFERRERS = 6;

/** FACT_ 접두사만 떼서 팩트/마스터 구분은 유지하면서 짧게 보여준다. */
function shortName(id: string): string {
  return id.startsWith("FACT_") ? id.slice(5) : id;
}

function firstLineValue(context: string): string {
  const line = context.split("\n")[0] ?? "";
  const colon = line.indexOf(":");
  return (colon >= 0 ? line.slice(colon + 1) : line).trim();
}

export default function SchemaPanel({ collectionName, domainContext, onSelectTable }: Props) {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [state, setState] = useState<"loading" | "ready" | "failed">("loading");
  const [asOf, setAsOf] = useState("");

  useEffect(() => {
    setAsOf(
      new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium" }).format(new Date())
    );
  }, []);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}` +
            `/api/graph/data?collection_name=${encodeURIComponent(collectionName)}`
        );
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        if (!alive) return;
        setNodes(data.nodes ?? []);
        setEdges(data.edges ?? []);
        setState("ready");
      } catch {
        if (alive) setState("failed");
      }
    })();
    return () => { alive = false; };
  }, [collectionName]);

  const { hubs, isolated, maxCount } = useMemo(() => {
    const inbound = new Map<string, string[]>();
    const touched = new Set<string>();

    for (const edge of edges) {
      if (!edge.source || !edge.target) continue;
      touched.add(edge.source);
      touched.add(edge.target);
      const list = inbound.get(edge.target) ?? [];
      list.push(edge.source);
      inbound.set(edge.target, list);
    }

    // tsconfig target 이 낮아 Map 스프레드가 막힌다 — Array.from 으로 순회한다.
    const ranked: Hub[] = Array.from(inbound.entries())
      .map(([id, referrers]) => ({ id, count: referrers.length, referrers }))
      .sort((a, b) => b.count - a.count || a.id.localeCompare(b.id));

    return {
      hubs: ranked,
      isolated: nodes.map((n) => n.id).filter((id) => !touched.has(id)),
      maxCount: ranked[0]?.count ?? 1,
    };
  }, [nodes, edges]);

  const specs: Array<[string, string]> = [
    ["도메인", firstLineValue(domainContext) || "미지정"],
    ["컬렉션", collectionName],
    ["테이블", state === "ready" ? `${nodes.length}` : "—"],
    ["조인", state === "ready" ? `${edges.length}` : "—"],
    ["기준", asOf || "—"],
  ];

  return (
    <section className="border border-rule bg-sheet">
      {/* 사양 블록 — 라벨/값 한 줄. 장식이 아니라 실제 적재 결과다. */}
      <dl className="grid grid-cols-2 gap-x-8 gap-y-3 px-6 py-5 sm:grid-cols-3 lg:grid-cols-5">
        {specs.map(([label, value], i) => (
          <div key={label} className="seq-lift min-w-0" style={{ "--d": `${i * 45}ms` } as React.CSSProperties}>
            <dt className="font-data text-[10px] tracking-[0.02em] text-ink3">
              {label}
            </dt>
            <dd className="mt-1 truncate font-data text-[13px] tabular-nums text-ink" title={value}>
              {value}
            </dd>
          </div>
        ))}
      </dl>

      <div className="seq-rule h-px bg-rule" />

      {/* 참조 허브 */}
      <div className="px-6 py-5">
        <div className="flex items-baseline justify-between gap-4">
          <h2 className="font-data text-[10px] tracking-[0.02em] text-ink3">
            참조 허브
          </h2>
          <p className="break-keep text-[11px] text-ink2">
            팩트 테이블이 가장 많이 참조하는 마스터 순
          </p>
        </div>

        {state === "loading" && (
          <p className="mt-4 text-[13px] text-ink2">스키마를 읽는 중입니다.</p>
        )}

        {state === "failed" && (
          <p className="mt-4 max-w-[56ch] break-keep text-[13px] text-crit">
            스키마를 불러오지 못했습니다. 지식 그래프 탭에서 새로고침을 눌러 다시 시도하세요.
          </p>
        )}

        {state === "ready" && hubs.length === 0 && (
          <p className="mt-4 max-w-[56ch] break-keep text-[13px] text-ink2">
            테이블 사이 연결이 없습니다. CSV의 외래키 컬럼명이 참조 테이블명과 맞는지 확인하세요.
          </p>
        )}

        {state === "ready" && hubs.length > 0 && (
          <ul className="mt-4 flex flex-col gap-3">
            {hubs.map((hub, i) => (
              <li
                key={hub.id}
                className="seq-lift grid grid-cols-[minmax(9rem,auto)_5rem_1fr] items-center gap-x-4 gap-y-1 max-sm:grid-cols-[1fr_auto]"
                style={{ "--d": `${180 + i * 55}ms` } as React.CSSProperties}
              >
                <button
                  type="button"
                  onClick={() => onSelectTable?.(hub.id)}
                  className="justify-self-start font-data text-[13px] text-ink underline-offset-4 transition hover:text-watch hover:underline focus-visible:rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-watch"
                >
                  {hub.id}
                </button>

                <div className="flex items-center gap-2 max-sm:justify-self-end">
                  <span
                    className="seq-bar h-[3px] w-14 bg-watch"
                    style={{ "--bar": hub.count / maxCount, "--d": `${240 + i * 55}ms` } as React.CSSProperties}
                  />
                  <span className="font-data text-[12px] tabular-nums text-ink2">{hub.count}</span>
                </div>

                <p className="font-data text-[11px] leading-relaxed text-ink3 max-sm:col-span-2">
                  {hub.referrers.slice(0, MAX_REFERRERS).map(shortName).join(" · ")}
                  {hub.referrers.length > MAX_REFERRERS && ` · 외 ${hub.referrers.length - MAX_REFERRERS}`}
                </p>
              </li>
            ))}
          </ul>
        )}

        {state === "ready" && isolated.length > 0 && (
          <p className="mt-4 border-t border-rule2 pt-3 font-data text-[11px] text-crit">
            고립 {isolated.length} · {isolated.join(" · ")}
            <span className="ml-2 font-ui text-ink2">외래키가 어느 테이블과도 맞지 않습니다.</span>
          </p>
        )}
      </div>
    </section>
  );
}
