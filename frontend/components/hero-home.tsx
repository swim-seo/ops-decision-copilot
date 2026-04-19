import PageIllustration from "@/components/page-illustration";

export default function HeroHome() {
  return (
    <section className="relative">
      <PageIllustration />
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="pb-12 pt-32 md:pb-20 md:pt-40">
          <div className="pb-12 text-center md:pb-16">

            <div
              className="mb-6 inline-flex items-center gap-2 rounded-full border border-amber-100 bg-amber-50 px-4 py-1.5 text-sm font-medium text-amber-600"
              data-aos="zoom-y-out"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse" />
              Claude AI · Anthropic 기반
            </div>

            <h1
              className="mb-6 border-y text-5xl font-bold [border-image:linear-gradient(to_right,transparent,--theme(--color-slate-300/.8),transparent)1] md:text-6xl"
              data-aos="zoom-y-out"
              data-aos-delay={150}
            >
              흩어진 운영 데이터를 연결하고,{" "}
              <br className="max-lg:hidden" />
              무엇을 해야 할지 짚어줍니다.
            </h1>

            <div className="mx-auto max-w-3xl">
              <p
                className="mb-8 text-lg text-gray-700"
                data-aos="zoom-y-out"
                data-aos-delay={300}
              >
                CSV, PDF, 엑셀 파일을 올리면 끝입니다. Ops Copilot이 지식 그래프를 자동으로 구성하고
                위험 요소를 감지해서, 다음 회의 전에 무엇을 해야 할지 정확히 알려줍니다.
              </p>

              <div className="relative before:absolute before:inset-0 before:border-y before:[border-image:linear-gradient(to_right,transparent,--theme(--color-slate-300/.8),transparent)1]">
                <div
                  className="mx-auto max-w-xs sm:flex sm:max-w-none sm:justify-center gap-3"
                  data-aos="zoom-y-out"
                  data-aos-delay={450}
                >
                  <a
                    className="btn group mb-4 w-full bg-linear-to-t from-amber-600 to-amber-500 bg-[length:100%_100%] bg-[bottom] text-white shadow-sm hover:bg-[length:100%_150%] sm:mb-0 sm:w-auto"
                    href="/app">
                    <span className="relative inline-flex items-center">
                      지금 바로 사용하기{" "}
                      <span className="ml-1 tracking-normal text-amber-300 transition-transform group-hover:translate-x-0.5">
                        -&gt;
                      </span>
                    </span>
                  </a>
                  <a
                    className="btn w-full bg-white text-gray-800 shadow-sm hover:bg-gray-50 sm:w-auto"
                    href="https://github.com/swim-seo/ops-decision-copilot"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    GitHub 보기
                  </a>
                </div>
              </div>

              <div
                className="mt-8 flex flex-wrap items-center justify-center gap-x-8 gap-y-2 text-sm text-gray-500"
                data-aos="zoom-y-out"
                data-aos-delay={550}
              >
                {["신용카드 불필요", "2분이면 시작 가능", "7개 산업 도메인 지원"].map((t) => (
                  <span key={t} className="flex items-center gap-1.5">
                    <svg className="h-4 w-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    {t}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div
            className="mx-auto max-w-3xl"
            data-aos="zoom-y-out"
            data-aos-delay={600}
          >
            <div className="relative aspect-video rounded-2xl bg-slate-900 px-5 py-4 shadow-xl before:pointer-events-none before:absolute before:-inset-5 before:border-y before:[border-image:linear-gradient(to_right,transparent,--theme(--color-slate-300/.8),transparent)1] after:absolute after:-inset-5 after:-z-10 after:border-x after:[border-image:linear-gradient(to_bottom,transparent,--theme(--color-slate-300/.8),transparent)1]">

              <div className="mb-4 flex items-center justify-between">
                <div className="flex gap-1.5">
                  <div className="h-2.5 w-2.5 rounded-full bg-red-500/70" />
                  <div className="h-2.5 w-2.5 rounded-full bg-yellow-500/70" />
                  <div className="h-2.5 w-2.5 rounded-full bg-green-500/70" />
                </div>
                <span className="text-[11px] font-medium text-gray-400">Ops Copilot · 일일 브리핑</span>
                <div className="w-12" />
              </div>

              <div className="grid grid-cols-3 gap-2.5 mb-3">
                {[
                  { label: "재고 위험", color: "text-red-400", bg: "bg-red-500/10 border-red-500/20", title: "안전재고 미달 SKU 3건", val: "PRD001 · PRD002 · PRD007" },
                  { label: "상위 성과", color: "text-green-400", bg: "bg-green-500/10 border-green-500/20", title: "선크림 MoM +38%", val: "D2C 채널 · 여름 성수기" },
                  { label: "이상 감지", color: "text-yellow-400", bg: "bg-yellow-500/10 border-yellow-500/20", title: "리드타임 +6일 편차", val: "SUP001 · CosmeLab" },
                ].map((card, i) => (
                  <div key={i} className={`rounded-lg border ${card.bg} p-2.5`}>
                    <p className={`text-[9px] font-semibold uppercase tracking-wider ${card.color} mb-1`}>{card.label}</p>
                    <p className="text-[11px] font-semibold text-white leading-tight mb-0.5">{card.title}</p>
                    <p className="text-[9px] text-gray-400">{card.val}</p>
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-2 rounded-lg border border-gray-700 bg-gray-800/60 px-3 py-2">
                <span className="text-amber-400 text-xs">◈</span>
                <span className="text-[11px] text-gray-400 font-mono flex-1">
                  "이번 주 긴급 발주가 필요한 SKU 알려줘"
                </span>
                <span className="text-[10px] text-gray-600 border border-gray-700 rounded px-1.5 py-0.5">⏎</span>
              </div>

              <div className="mt-2 rounded-lg bg-amber-500/10 border border-amber-500/20 px-3 py-2">
                <p className="text-[10px] text-amber-300 font-mono leading-relaxed">
                  <span className="text-amber-400 font-semibold">Copilot: </span>
                  PRD001, PRD002 안전재고 미달입니다. SUP001 리드타임 14일 — 다음 주 입고를 위해 오늘 발주하세요.
                  <span className="ml-1 inline-block h-3 w-0.5 bg-amber-400 animate-pulse" />
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
