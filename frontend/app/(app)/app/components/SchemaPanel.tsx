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
interface GraphEdge {
  source: string;
  target: string;
  relation?: string;
  join_key?: string;
  join_keys?: string[];
}
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

  /**
   * 조인 키 매트릭스 — 행은 참조하는 쪽(주로 팩트), 열은 참조받는 쪽(주로 마스터),
   * 칸은 그 둘을 잇는 외래키다.
   *
   * 노드-링크 그래프로는 "이 팩트를 저 마스터에 무슨 키로 붙이지?" 를 한 번에 못 읽는다.
   * 조회형 질문이라 표가 맞다. 열은 참조 많은 순이라 첫 열이 곧 이 스키마의 축이다.
   *
   * 행을 팩트로만 제한하지는 않는다 — MST_PRODUCT→MST_SUPPLIER 처럼 마스터끼리
   * 물리는 FK 가 실제로 있고, 그걸 빼면 표가 스키마를 온전히 설명하지 못한다.
   */
  const matrix = useMemo(() => {
    const keyOf = (e: GraphEdge): string => {
      const keys = e.join_keys?.length ? e.join_keys : e.join_key ? [e.join_key] : [];
      return keys.join(", ");
    };

    // 행 → (열 → 조인키). 두 이름을 한 문자열로 이어 붙여 키를 만들면 구분자가
    // 조용히 어긋났을 때 표 전체가 빈 칸으로 나오고 원인이 보이지 않는다.
    const cells = new Map<string, Map<string, string>>();
    const inboundCount = new Map<string, number>();

    for (const edge of edges) {
      if (!edge.source || !edge.target) continue;
      const key = keyOf(edge);
      // 키를 모르는 연결은 칸을 채우지 않는다. 빈 칸이 "연결 없음" 을 뜻해야
      // 표가 읽히는데, 키 없는 연결까지 칠하면 그 구분이 무너진다.
      if (!key) continue;
      const row = cells.get(edge.source) ?? new Map<string, string>();
      row.set(edge.target, key);
      cells.set(edge.source, row);
      inboundCount.set(edge.target, (inboundCount.get(edge.target) ?? 0) + 1);
    }

    const cols = Array.from(inboundCount.entries())
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .map(([id]) => id);

    // 팩트를 위로 올린다. 읽는 사람은 "무엇을 무엇에 붙이나" 를 팩트 기준으로 본다.
    const rank = (id: string) => (id.startsWith("FACT_") ? 0 : 1);
    const rows = Array.from(cells.keys()).sort(
      (a, b) => rank(a) - rank(b) || a.localeCompare(b)
    );

    return { rows, cols, cells };
  }, [edges]);

  // mono 는 ASCII 값에만 쓴다. 도메인명은 한글이라 mono 로 두면 글리프가 없어
  // 공백 폭만 mono 를 따라가고 자간이 벌어진다.
  const specs: Array<{ label: string; value: string; mono: boolean }> = [
    { label: "도메인", value: firstLineValue(domainContext) || "미지정", mono: false },
    { label: "컬렉션", value: collectionName, mono: true },
    { label: "테이블", value: state === "ready" ? `${nodes.length}` : "—", mono: true },
    { label: "조인", value: state === "ready" ? `${edges.length}` : "—", mono: true },
    { label: "기준", value: asOf || "—", mono: true },
  ];

  return (
    <section className="border border-rule bg-sheet">
      {/* 사양 블록 — 라벨/값 한 줄. 장식이 아니라 실제 적재 결과다. */}
      <dl className="grid grid-cols-2 gap-x-8 gap-y-3 px-6 py-5 sm:grid-cols-3 lg:grid-cols-5">
        {specs.map(({ label, value, mono }, i) => (
          <div key={label} className="seq-lift min-w-0" style={{ "--d": `${i * 45}ms` } as React.CSSProperties}>
            <dt className="font-ui text-[11px] font-medium tracking-[0.02em] text-ink3">
              {label}
            </dt>
            <dd
              className={`mt-1 truncate text-[13px] tabular-nums text-ink ${mono ? "font-data" : "font-ui"}`}
              title={value}
            >
              {value}
            </dd>
          </div>
        ))}
      </dl>

      <div className="seq-rule h-px bg-rule" />

      {/* 조인 키 매트릭스 */}
      {state === "ready" && matrix.rows.length > 0 && (
        <div className="px-6 py-5">
          <div className="flex items-baseline justify-between gap-4">
            <h2 className="font-ui text-[11px] font-medium tracking-[0.02em] text-ink3">
              조인 키
            </h2>
            <p className="break-keep text-[11px] text-ink2">
              행을 열에 붙일 때 쓰는 외래키
            </p>
          </div>

          {/* 열이 늘어나면 표만 가로로 흐르게 한다 — 페이지가 밀리면 안 된다. */}
          <div className="mt-4 overflow-x-auto">
            <table className="w-full border-collapse text-left">
              <thead>
                <tr>
                  <th scope="col" className="sr-only">
                    참조하는 테이블
                  </th>
                  {matrix.cols.map((col, i) => (
                    <th
                      key={col}
                      scope="col"
                      className={`whitespace-nowrap border-b border-rule px-3 py-2 font-data text-[12px] font-normal ${
                        i === 0 ? "bg-rule2 text-ink" : "text-ink2"
                      }`}
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {matrix.rows.map((row, r) => (
                  <tr
                    key={row}
                    className="seq-lift"
                    style={{ "--d": `${120 + r * 40}ms` } as React.CSSProperties}
                  >
                    <th
                      scope="row"
                      className="whitespace-nowrap border-b border-rule2 py-2 pr-4 font-data text-[13px] font-normal text-ink"
                    >
                      <button
                        type="button"
                        onClick={() => onSelectTable?.(row)}
                        className="underline-offset-4 transition hover:text-watch hover:underline focus-visible:rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-watch"
                      >
                        {row}
                      </button>
                    </th>
                    {matrix.cols.map((col, i) => {
                      const key = matrix.cells.get(row)?.get(col);
                      return (
                        <td
                          key={col}
                          className={`whitespace-nowrap border-b border-rule2 px-3 py-2 font-data text-[12px] ${
                            i === 0 ? "bg-rule2" : ""
                          } ${key ? "text-ink2" : "text-ink3"}`}
                        >
                          {key || <span aria-label="연결 없음">·</span>}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {state === "ready" && matrix.rows.length > 0 && (
        <div className="seq-rule h-px bg-rule" />
      )}

      {/* 참조 허브 */}
      <div className="px-6 py-5">
        <div className="flex items-baseline justify-between gap-4">
          <h2 className="font-ui text-[11px] font-medium tracking-[0.02em] text-ink3">
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
