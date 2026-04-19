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
        <div className="mb-1 inline-flex items-center gap-2 rounded-full border border-amber-500/20 bg-amber-500/5 px-3 py-1 text-xs font-medium text-amber-500">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
          Step 2 of 2
        </div>
        <h1 className="mt-4 text-3xl font-bold tracking-tight text-white">데이터를 불러오세요</h1>
        <p className="mt-2 text-slate-500">샘플로 바로 체험하거나 직접 파일을 업로드하세요.</p>
      </div>

      {/* Matched sample */}
      {matched && (
        <div className="mb-5">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-amber-500/70">추천 샘플</p>
          <button
            onClick={() => handleSample(matched.id)}
            disabled={loading}
            className="group w-full rounded-xl border border-amber-500/20 bg-gradient-to-br from-amber-500/10 to-transparent p-4 text-left transition hover:border-amber-500/40 hover:from-amber-500/15 disabled:opacity-40"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold text-white">{matched.label}</p>
                <p className="mt-0.5 text-xs text-slate-500">{matched.description}</p>
              </div>
              <span className="ml-4 shrink-0 rounded-lg bg-amber-500 px-4 py-2 text-xs font-bold text-slate-900 transition group-hover:bg-amber-400">
                시작하기
              </span>
            </div>
          </button>
        </div>
      )}

      {/* Other samples */}
      {others.length > 0 && (
        <div className="mb-6">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-slate-600">
            {matched ? "다른 샘플" : "샘플 데이터"}
          </p>
          <div className="grid grid-cols-3 gap-2">
            {others.map((s) => (
              <button
                key={s.id}
                onClick={() => handleSample(s.id)}
                disabled={loading}
                className="rounded-lg border border-white/[0.06] bg-white/[0.03] p-3 text-left transition hover:border-white/10 hover:bg-white/[0.05] disabled:opacity-40"
              >
                <p className="text-xs font-medium text-slate-300">{s.label}</p>
                <p className="mt-0.5 text-[10px] leading-relaxed text-slate-600">{s.description}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="relative my-5 flex items-center gap-3">
        <div className="h-px flex-1 bg-white/[0.06]" />
        <span className="text-[11px] text-slate-700">또는 직접 업로드</span>
        <div className="h-px flex-1 bg-white/[0.06]" />
      </div>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e: DragEvent) => { e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files); }}
        onClick={() => inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center gap-2 rounded-xl border-2 border-dashed px-6 py-10 transition-all ${
          dragging ? "border-amber-500/60 bg-amber-500/5" : "border-white/[0.08] hover:border-white/[0.14] hover:bg-white/[0.02]"
        }`}
      >
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.04]">
          <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5 text-slate-500">
            <path fillRule="evenodd" d="M9.25 7a.75.75 0 01.75-.75h.008a.75.75 0 01.75.75v.008a.75.75 0 01-.75.75H10a.75.75 0 01-.75-.75V7zM9.25 10.5A.75.75 0 0110 9.75h.008a.75.75 0 01.75.75v2.5a.75.75 0 01-1.5 0V10.5H10A.75.75 0 019.25 10.5z" clipRule="evenodd"/>
            <path fillRule="evenodd" d="M3 10a7 7 0 1114 0 7 7 0 01-14 0zm7-8.5a8.5 8.5 0 100 17 8.5 8.5 0 000-17z" clipRule="evenodd"/>
          </svg>
        </div>
        <p className="text-sm text-slate-400">파일을 드래그하거나 <span className="text-amber-400">클릭해서 선택</span></p>
        <p className="text-xs text-slate-700">CSV · Excel · PDF · DOCX · TXT · MD</p>
        <input ref={inputRef} type="file" multiple accept=".csv,.xlsx,.pdf,.docx,.txt,.md,.json,.py" className="hidden" onChange={(e) => addFiles(e.target.files)} />
      </div>

      {files.length > 0 && (
        <>
          <ul className="mt-3 space-y-1.5">
            {files.map((f) => (
              <li key={f.name} className="flex items-center gap-3 rounded-lg border border-white/[0.06] bg-white/[0.03] px-3 py-2 text-xs">
                <svg viewBox="0 0 16 16" fill="currentColor" className="h-3.5 w-3.5 shrink-0 text-slate-600">
                  <path d="M4 1.75C4 .784 4.784 0 5.75 0h5.586c.464 0 .909.184 1.237.513l2.914 2.914c.329.328.513.773.513 1.237v8.586A1.75 1.75 0 0114.25 15h-8.5A1.75 1.75 0 014 13.25V1.75z"/>
                </svg>
                <span className="flex-1 truncate text-slate-400">{f.name}</span>
                <span className="text-slate-600">{(f.size / 1024).toFixed(0)}KB</span>
                <button onClick={() => setFiles((p) => p.filter((x) => x.name !== f.name))} className="text-slate-700 hover:text-red-400">✕</button>
              </li>
            ))}
          </ul>
          <button
            onClick={handleUpload}
            disabled={loading}
            className="mt-4 w-full rounded-xl bg-amber-500 py-3 text-sm font-semibold text-slate-900 transition hover:bg-amber-400 disabled:opacity-40"
          >
            {loading ? progress : `${files.length}개 파일 분석 시작`}
          </button>
        </>
      )}

      {loading && (
        <div className="mt-4 flex items-center justify-center gap-2 text-xs text-slate-500">
          <svg className="h-3.5 w-3.5 animate-spin text-amber-500" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z"/>
          </svg>
          {progress}
        </div>
      )}
    </div>
  );
}
