"use client";

import { useState } from "react";
import Link from "next/link";
import DomainSelector from "./components/DomainSelector";
import FileUpload from "./components/FileUpload";
import BriefingCards from "./components/BriefingCards";
import GraphViewer from "./components/GraphViewer";
import ChatWidget from "./components/ChatWidget";

type Step = "domain" | "upload" | "results";
type ResultTab = "briefing" | "graph";

const NAV = [
  { id: "briefing" as ResultTab, label: "브리핑", icon: (
    <svg viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
      <path fillRule="evenodd" d="M2 4.75A.75.75 0 012.75 4h14.5a.75.75 0 010 1.5H2.75A.75.75 0 012 4.75zm0 10.5a.75.75 0 01.75-.75h7.5a.75.75 0 010 1.5h-7.5a.75.75 0 01-.75-.75zM2 10a.75.75 0 01.75-.75h14.5a.75.75 0 010 1.5H2.75A.75.75 0 012 10z" clipRule="evenodd"/>
    </svg>
  )},
  { id: "graph" as ResultTab, label: "지식 그래프", icon: (
    <svg viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
      <path d="M13.024 9.25c.47 0 .827-.423.734-.883a4.501 4.501 0 00-3.626-3.625.734.734 0 00-.883.734v.022a.75.75 0 00.631.74 3 3 0 012.12 2.12.75.75 0 00.739.632h.285z"/>
      <path fillRule="evenodd" d="M12 2.25A7.75 7.75 0 104.785 14.28l-2.017 2.017a.75.75 0 101.06 1.06L5.845 15.34A7.75 7.75 0 0012 2.25zm-6.25 7.75a6.25 6.25 0 1112.5 0 6.25 6.25 0 01-12.5 0z" clipRule="evenodd"/>
    </svg>
  )},
];

const STEPS = [
  { id: "domain", label: "도메인", num: 1 },
  { id: "upload", label: "업로드", num: 2 },
  { id: "results", label: "결과", num: 3 },
];

export default function AppPage() {
  const [step, setStep] = useState<Step>("domain");
  const [domainName, setDomainName] = useState("");
  const [collectionName, setCollectionName] = useState("");
  const [domainContext, setDomainContext] = useState("");
  const [activeTab, setActiveTab] = useState<ResultTab>("briefing");

  function handleDomainComplete(collection: string, context: string) {
    setCollectionName(collection);
    setDomainContext(context);
    setStep("upload");
  }

  function handleUploadComplete() {
    setStep("results");
  }

  const stepIndex = STEPS.findIndex((s) => s.id === step);

  return (
    <div className="flex min-h-screen flex-col bg-[#0a0a0f]">
      {/* Header */}
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-white/[0.06] px-6">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-500">
            <svg viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4 text-slate-900">
              <path d="M5.52.359A.75.75 0 016.106 0h3.788a.75.75 0 01.74.871l-.83 4.875h3.045a.75.75 0 01.595 1.207l-6.25 8.25a.75.75 0 01-1.304-.65l1.175-5.893H3.25a.75.75 0 01-.596-1.207L5.52.359z"/>
            </svg>
          </div>
          <span className="text-sm font-semibold text-white">Ops Copilot</span>
        </Link>

        {/* Stepper */}
        {step !== "results" && (
          <div className="flex items-center gap-1">
            {STEPS.map((s, i) => {
              const done = i < stepIndex;
              const active = i === stepIndex;
              return (
                <div key={s.id} className="flex items-center gap-1">
                  {i > 0 && <div className={`h-px w-8 transition-colors ${done ? "bg-amber-500/60" : "bg-white/10"}`} />}
                  <div className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium transition-all ${
                    active ? "bg-amber-500 text-slate-900" :
                    done ? "bg-amber-500/20 text-amber-500" :
                    "bg-white/5 text-slate-600"
                  }`}>
                    {done ? "✓" : s.num}
                  </div>
                  <span className={`hidden text-xs sm:block transition-colors ${active ? "text-white" : done ? "text-slate-500" : "text-slate-700"}`}>
                    {s.label}
                  </span>
                </div>
              );
            })}
          </div>
        )}

        <div className="w-24 text-right">
          {step === "results" && (
            <button
              onClick={() => setStep("upload")}
              className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-slate-400 transition hover:border-white/20 hover:text-white"
            >
              + 파일 추가
            </button>
          )}
        </div>
      </header>

      {/* Body */}
      {step !== "results" ? (
        <main className="flex flex-1 items-center justify-center p-6">
          <div className="w-full max-w-lg">
            {step === "domain" && <DomainSelector onComplete={handleDomainComplete} />}
            {step === "upload" && (
              <FileUpload
                collectionName={collectionName}
                domainName={domainName}
                onComplete={handleUploadComplete}
              />
            )}
          </div>
        </main>
      ) : (
        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <aside className="flex w-52 shrink-0 flex-col border-r border-white/[0.06] bg-[#0d0d14] p-3">
            <div className="mb-4 px-2 pt-2">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-600">분석 뷰</p>
            </div>
            <nav className="space-y-0.5">
              {NAV.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all ${
                    activeTab === item.id
                      ? "bg-amber-500/10 text-amber-400"
                      : "text-slate-500 hover:bg-white/[0.04] hover:text-slate-300"
                  }`}
                >
                  <span className={activeTab === item.id ? "text-amber-400" : "text-slate-600"}>
                    {item.icon}
                  </span>
                  {item.label}
                </button>
              ))}
            </nav>

            <div className="mt-auto border-t border-white/[0.06] pt-4">
              <div className="rounded-lg bg-white/[0.03] p-3">
                <p className="text-[10px] text-slate-600">컬렉션</p>
                <p className="mt-0.5 truncate text-xs font-medium text-slate-400">{collectionName}</p>
              </div>
            </div>
          </aside>

          {/* Content */}
          <main className="relative flex flex-1 flex-col overflow-hidden">
            <div className={activeTab !== "briefing" ? "hidden" : "flex-1 overflow-y-auto p-6"}>
              <BriefingCards collectionName={collectionName} domainContext={domainContext} />
            </div>
            <div className={activeTab !== "graph" ? "hidden" : "flex flex-1 flex-col overflow-hidden p-6"}>
              <GraphViewer collectionName={collectionName} />
            </div>
            <ChatWidget collectionName={collectionName} domainContext={domainContext} />
          </main>
        </div>
      )}
    </div>
  );
}
