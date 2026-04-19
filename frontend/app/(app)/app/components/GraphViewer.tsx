"use client";

import { useState } from "react";

interface Props { collectionName: string; }

export default function GraphViewer({ collectionName }: Props) {
  const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const url = `${BASE}/api/graph/html?collection_name=${encodeURIComponent(collectionName)}`;
  const [key, setKey] = useState(0);

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-white">지식 그래프</h2>
          <p className="text-xs text-slate-600">업로드된 문서의 구조와 관계를 시각화합니다</p>
        </div>
        <button
          onClick={() => setKey((k) => k + 1)}
          className="flex items-center gap-1.5 rounded-lg border border-white/[0.07] px-3 py-1.5 text-xs text-slate-500 transition hover:border-white/[0.12] hover:text-slate-300"
        >
          <svg viewBox="0 0 16 16" fill="currentColor" className="h-3.5 w-3.5">
            <path fillRule="evenodd" d="M8 2.5a5.487 5.487 0 00-4.131 1.869l1.204 1.204A.25.25 0 014.896 6H1.75A.25.25 0 011.5 5.75V2.604a.25.25 0 01.427-.177l1.38 1.38A7.001 7.001 0 0114.95 7.16a.75.75 0 11-1.49.178A5.501 5.501 0 008 2.5zM1.705 8.005a.75.75 0 01.834.656 5.501 5.501 0 009.592 2.97l-1.204-1.204a.25.25 0 01.177-.427h3.146a.25.25 0 01.25.25v3.146a.25.25 0 01-.427.177l-1.38-1.38A7.001 7.001 0 011.05 8.84a.75.75 0 01.656-.834z" clipRule="evenodd"/>
          </svg>
          새로고침
        </button>
      </div>

      <div className="flex-1 overflow-hidden rounded-xl border border-white/[0.06] bg-[#0d0d14]">
        <iframe
          key={key}
          src={url}
          className="h-full w-full"
          title="Knowledge Graph"
          sandbox="allow-scripts allow-same-origin"
        />
      </div>
    </div>
  );
}
