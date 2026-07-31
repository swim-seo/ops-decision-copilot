"use client";

import { useState } from "react";
import Link from "next/link";
import DomainSelector from "./components/DomainSelector";
import FileUpload from "./components/FileUpload";
import BriefingCards from "./components/BriefingCards";
import SchemaPanel from "./components/SchemaPanel";
import GraphViewer from "./components/GraphViewer";
import ChatWidget from "./components/ChatWidget";

type Step = "domain" | "upload" | "results";
type ResultTab = "briefing" | "graph";

const NAV: Array<{ id: ResultTab; label: string; note: string; mark: string }> = [
  { id: "briefing", label: "브리핑", note: "오늘 확인할 것", mark: "B" },
  { id: "graph", label: "지식 그래프", note: "테이블 연결 구조", mark: "G" },
];

const STEPS: Array<{ id: Step; label: string; num: number }> = [
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

  // 1단계에서 입력한 도메인명을 2단계까지 넘긴다. 예전엔 여기서 잃어버려서
  // 추천 샘플 매칭이 늘 실패하고 업로드 API 에 빈 도메인이 갔다.
  function handleDomainComplete(collection: string, context: string, name: string) {
    setCollectionName(collection);
    setDomainContext(context);
    setDomainName(name);
    setStep("upload");
  }

  const stepIndex = STEPS.findIndex((s) => s.id === step);

  return (
    <div className="flex min-h-screen flex-col bg-paper">
      <header className="flex h-14 shrink-0 items-center justify-between gap-4 border-b border-rule bg-sheet px-5">
        <Link
          href="/"
          className="flex items-center gap-2.5 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-watch"
        >
          <span className="flex h-7 w-7 items-center justify-center bg-signal">
            <svg viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4 text-sheet">
              <path d="M5.52.359A.75.75 0 016.106 0h3.788a.75.75 0 01.74.871l-.83 4.875h3.045a.75.75 0 01.595 1.207l-6.25 8.25a.75.75 0 01-1.304-.65l1.175-5.893H3.25a.75.75 0 01-.596-1.207L5.52.359z" />
            </svg>
          </span>
          <span className="font-display text-[15px] font-medium tracking-tight text-ink">
            Ops Copilot
          </span>
        </Link>

        {step !== "results" && (
          <ol className="flex items-center gap-1.5">
            {STEPS.map((s, i) => {
              const done = i < stepIndex;
              const active = i === stepIndex;
              return (
                <li key={s.id} className="flex items-center gap-1.5">
                  {i > 0 && <span className={`h-px w-7 ${done ? "bg-signal" : "bg-rule"}`} />}
                  <span
                    className={`flex h-5 w-5 items-center justify-center font-data text-[11px] tabular-nums ${
                      active
                        ? "bg-signal text-sheet"
                        : done
                          ? "bg-rule2 text-signal"
                          : "bg-rule2 text-ink3"
                    }`}
                  >
                    {done ? "✓" : s.num}
                  </span>
                  <span className={`hidden text-[12px] sm:block ${active ? "text-ink" : "text-ink3"}`}>
                    {s.label}
                  </span>
                </li>
              );
            })}
          </ol>
        )}

        <div className="min-w-24 text-right">
          {step === "results" && (
            <button
              type="button"
              onClick={() => setStep("upload")}
              className="border border-rule px-3 py-1.5 text-[12px] text-ink2 transition hover:border-ink3 hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-watch"
            >
              파일 추가
            </button>
          )}
        </div>
      </header>

      {step !== "results" ? (
        <main className="flex flex-1 items-center justify-center p-6">
          <div className="w-full max-w-lg">
            {step === "domain" && <DomainSelector onComplete={handleDomainComplete} />}
            {step === "upload" && (
              <FileUpload
                collectionName={collectionName}
                domainName={domainName}
                onComplete={() => setStep("results")}
              />
            )}
          </div>
        </main>
      ) : (
        <div className="flex flex-1 overflow-hidden">
          <aside className="flex w-56 shrink-0 flex-col px-3 py-4 max-lg:w-14 max-lg:px-1.5">
            <p className="px-2 font-ui text-[11px] font-medium tracking-[0.02em] text-ink3 max-lg:sr-only">
              분석 뷰
            </p>
            <nav className="mt-3 flex flex-col gap-0.5">
              {NAV.map((item) => {
                const active = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setActiveTab(item.id)}
                    aria-current={active ? "page" : undefined}
                    title={item.label}
                    className={`flex flex-col items-start gap-0.5 border-l-2 px-3 py-2 text-left transition max-lg:items-center max-lg:px-0 ${
                      active ? "border-signal bg-sheet" : "border-transparent hover:bg-sheet"
                    } focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-watch`}
                  >
                    <span className={`text-[13px] max-lg:sr-only ${active ? "text-ink" : "text-ink2"}`}>
                      {item.label}
                    </span>
                    <span className="font-ui text-[11px] text-ink3 max-lg:hidden">{item.note}</span>
                    <span
                      className="hidden font-data text-[11px] text-ink2 max-lg:block"
                      aria-hidden="true"
                    >
                      {item.mark}
                    </span>
                  </button>
                );
              })}
            </nav>

            <div className="mt-auto border-t border-rule pt-3 max-lg:hidden">
              <p className="font-ui text-[11px] font-medium tracking-[0.02em] text-ink3">컬렉션</p>
              <p className="mt-1 truncate font-data text-[12px] text-ink2" title={collectionName}>
                {collectionName}
              </p>
            </div>
          </aside>

          <main className="relative flex flex-1 flex-col overflow-hidden border-l border-rule">
            <div
              className={
                activeTab === "briefing" ? "flex flex-1 flex-col gap-4 overflow-y-auto p-6" : "hidden"
              }
            >
              <BriefingCards collectionName={collectionName} domainContext={domainContext} />
              <SchemaPanel
                collectionName={collectionName}
                domainContext={domainContext}
                onSelectTable={() => setActiveTab("graph")}
              />
            </div>

            <div
              className={activeTab === "graph" ? "flex flex-1 flex-col overflow-hidden p-6" : "hidden"}
            >
              <GraphViewer collectionName={collectionName} />
            </div>

            <ChatWidget collectionName={collectionName} domainContext={domainContext} />
          </main>
        </div>
      )}
    </div>
  );
}
