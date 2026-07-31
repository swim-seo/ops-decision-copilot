"use client";

import { useState, useRef, DragEvent, useEffect } from "react";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface Sample { id: string; label: string; description: string; keywords: string[]; }
interface Props { collectionName: string; domainName: string; onComplete: () => void; }

export default function FileUpload({ collectionName, domainName, onComplete }: Props) {
  const [files, setFiles] = useState<File[]>([]);
  const [samples, setSamples] = useState<Sample[]>([]);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState("");
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetch(`${BASE}/api/upload/samples`).then((r) => r.json()).then(setSamples).catch(() => {});
  }, []);

  function addFiles(list: FileList | null) {
    if (!list) return;
    const arr = Array.from(list);
    setFiles((p) => { const names = new Set(p.map((f) => f.name)); return [...p, ...arr.filter((f) => !names.has(f.name))]; });
  }

  async function handleUpload() {
    if (!files.length) return;
    setLoading(true); setProgress("업로드 중...");
    try {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      form.append("domain_name", domainName);
      form.append("collection_name", collectionName);
      const res = await fetch(`${BASE}/api/upload/files`, { method: "POST", body: form });
      if (!res.ok) throw new Error(await res.text());
      setTimeout(onComplete, 400);
    } catch (e) { alert("업로드 실패: " + e); setLoading(false); setProgress(""); }
  }

  async function handleSample(id: string) {
    setLoading(true); setProgress("샘플 불러오는 중...");
    try {
      const res = await fetch(`${BASE}/api/upload/sample`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sample_id: id, collection_name: collectionName }),
      });
      if (!res.ok) throw new Error(await res.text());
      setTimeout(onComplete, 400);
    } catch (e) { alert("샘플 로드 실패: " + e); setLoading(false); setProgress(""); }
  }

  const matched = samples.find((s) => s.keywords.some((k) => domainName.toLowerCase().includes(k.toLowerCase())));
  const others = samples.filter((s) => s.id !== matched?.id);

  return (
    <div>
      <div className="mb-8">
        <div className="inline-flex items-center gap-2 border border-signal/30 bg-signal/5 px-2.5 py-1 font-ui text-[11px] font-medium tracking-[0.02em] text-signal">
          <span className="h-1.5 w-1.5 bg-signal" />
          2단계 · 업로드
        </div>
        <h1 className="mt-4 font-display text-[30px] font-medium leading-tight tracking-tight text-balance break-keep text-ink">데이터를 불러오세요</h1>
        <p className="mt-2 max-w-[42ch] break-keep text-[14px] text-ink2">샘플 데이터로 바로 확인하거나, 직접 파일을 올리세요.</p>
      </div>

      {/* Matched sample */}
      {matched && (
        <div className="mb-5">
          <p className="mb-2 font-ui text-[11px] font-medium tracking-[0.02em] text-ink3">추천 샘플</p>
          <button
            onClick={() => handleSample(matched.id)}
            disabled={loading}
            className="w-full border border-signal/30 bg-signal/5 p-4 text-left transition hover:border-signal hover:bg-signal/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-watch disabled:opacity-40"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold text-ink">{matched.label}</p>
                <p className="mt-0.5 text-xs text-ink3">{matched.description}</p>
              </div>
              <span className="ml-4 shrink-0 bg-ink px-4 py-2 text-xs font-semibold text-paper">
                시작하기
              </span>
            </div>
          </button>
        </div>
      )}

      {/* Other samples */}
      {others.length > 0 && (
        <div className="mb-6">
          <p className="mb-2 font-ui text-[11px] font-medium tracking-[0.02em] text-ink3">
            {matched ? "다른 샘플" : "샘플 데이터"}
          </p>
          <div className="grid grid-cols-3 gap-2">
            {others.map((s) => (
              <button
                key={s.id}
                onClick={() => handleSample(s.id)}
                disabled={loading}
                className="border border-rule bg-sheet p-3 text-left transition hover:border-ink3 hover:bg-rule2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-watch disabled:opacity-40"
              >
                <p className="text-xs font-medium text-ink">{s.label}</p>
                <p className="mt-0.5 text-[10px] leading-relaxed text-ink3">{s.description}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="relative my-5 flex items-center gap-3">
        <div className="h-px flex-1 bg-rule" />
        <span className="font-ui text-[11px] font-medium tracking-[0.02em] text-ink3">또는 직접 업로드</span>
        <div className="h-px flex-1 bg-rule" />
      </div>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e: DragEvent) => { e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files); }}
        onClick={() => inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center gap-2 border border-dashed px-6 py-10 transition ${
          dragging ? "border-signal bg-signal/5" : "border-rule bg-sheet hover:border-ink3 hover:bg-rule2"
        }`}
      >
        <div className="flex h-10 w-10 items-center justify-center bg-rule2">
          <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5 text-ink2">
            <path fillRule="evenodd" d="M9.25 7a.75.75 0 01.75-.75h.008a.75.75 0 01.75.75v.008a.75.75 0 01-.75.75H10a.75.75 0 01-.75-.75V7zM9.25 10.5A.75.75 0 0110 9.75h.008a.75.75 0 01.75.75v2.5a.75.75 0 01-1.5 0V10.5H10A.75.75 0 019.25 10.5z" clipRule="evenodd"/>
            <path fillRule="evenodd" d="M3 10a7 7 0 1114 0 7 7 0 01-14 0zm7-8.5a8.5 8.5 0 100 17 8.5 8.5 0 000-17z" clipRule="evenodd"/>
          </svg>
        </div>
        <p className="text-sm text-ink2">파일을 드래그하거나 <span className="text-signal">클릭해서 선택</span></p>
        <p className="font-data text-[10px] text-ink3">CSV · XLSX · PDF · DOCX · TXT · MD</p>
        <input ref={inputRef} type="file" multiple accept=".csv,.xlsx,.pdf,.docx,.txt,.md,.json,.py" className="hidden" onChange={(e) => addFiles(e.target.files)} />
      </div>

      {files.length > 0 && (
        <>
          <ul className="mt-3 space-y-1.5">
            {files.map((f) => (
              <li key={f.name} className="flex items-center gap-3 border border-rule bg-sheet px-3 py-2 text-xs">
                <svg viewBox="0 0 16 16" fill="currentColor" className="h-3.5 w-3.5 shrink-0 text-ink2">
                  <path d="M4 1.75C4 .784 4.784 0 5.75 0h5.586c.464 0 .909.184 1.237.513l2.914 2.914c.329.328.513.773.513 1.237v8.586A1.75 1.75 0 0114.25 15h-8.5A1.75 1.75 0 014 13.25V1.75z"/>
                </svg>
                <span className="flex-1 truncate text-ink2">{f.name}</span>
                <span className="font-data tabular-nums text-ink3">{(f.size / 1024).toFixed(0)}KB</span>
                <button onClick={() => setFiles((p) => p.filter((x) => x.name !== f.name))} className="text-ink3 transition hover:text-crit focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-watch" aria-label="목록에서 제거">✕</button>
              </li>
            ))}
          </ul>
          <button
            onClick={handleUpload}
            disabled={loading}
            className="mt-4 w-full bg-ink py-3 text-sm font-semibold text-paper transition hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-watch disabled:opacity-40"
          >
            {loading ? progress : `${files.length}개 파일 분석 시작`}
          </button>
        </>
      )}

      {loading && (
        <div className="mt-4 flex items-center justify-center gap-2 text-xs text-ink2">
          <svg className="h-3.5 w-3.5 animate-spin text-signal" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z"/>
          </svg>
          {progress}
        </div>
      )}
    </div>
  );
}
