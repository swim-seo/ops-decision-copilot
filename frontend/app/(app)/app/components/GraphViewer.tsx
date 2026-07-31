"use client";

import { useState } from "react";

interface Props { collectionName: string }

/** 그래프는 백엔드(pyvis)가 렌더한 HTML을 iframe으로 싣는다.
 *  범례의 색·도형은 서버가 실제로 그리는 값과 같아야 하므로 hex를 그대로 적는다. */
const LEGEND: Array<{ shape: "diamond" | "ellipse"; color: string; label: string }> = [
  { shape: "diamond", color: "#7C3AED", label: "마스터 테이블" },
  { shape: "ellipse", color: "#2563EB", label: "팩트 테이블" },
];

export default function GraphViewer({ collectionName }: Props) {
  const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const url = `${BASE}/api/graph/html?collection_name=${encodeURIComponent(collectionName)}`;
  const [key, setKey] = useState(0);

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
        <div>
          <h2 className="font-display text-[17px] font-medium text-ink">군집 보기</h2>
          <p className="mt-1 max-w-[52ch] break-keep text-[12px] text-ink2">
            위가 팩트, 아래가 참조받는 마스터입니다. 선 위 이름이 조인 키이고,
            테이블을 클릭하면 컬럼과 연결 관계가 열립니다.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setKey((k) => k + 1)}
          className="border border-rule px-3 py-1.5 font-ui text-[11px] text-ink2 transition hover:border-ink3 hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-watch"
        >
          다시 그리기
        </button>
      </div>

      <ul className="flex flex-wrap items-center gap-x-5 gap-y-2">
        {LEGEND.map((item) => (
          <li key={item.label} className="flex items-center gap-2">
            <span
              aria-hidden="true"
              className={`h-2.5 w-2.5 ${item.shape === "diamond" ? "rotate-45" : "rounded-full"}`}
              style={{ backgroundColor: item.color }}
            />
            <span className="font-ui text-[11px] text-ink2">{item.label}</span>
          </li>
        ))}
        <li className="flex items-center gap-2">
          <span aria-hidden="true" className="font-data text-[13px] leading-none text-ink3">
            &rarr;
          </span>
          <span className="font-ui text-[11px] text-ink2">참조 방향 (팩트 &rarr; 마스터)</span>
        </li>
      </ul>

      <div className="flex-1 overflow-hidden border border-rule bg-sheet">
        <iframe
          key={key}
          src={url}
          className="h-full w-full"
          title="테이블 연결 구조"
          sandbox="allow-scripts allow-same-origin"
        />
      </div>
    </div>
  );
}
