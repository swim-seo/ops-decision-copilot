export default function HowItWorks() {
  const steps = [
    {
      num: "01",
      title: "데이터 업로드",
      desc: "CSV, PDF, 엑셀, 문서 파일을 그냥 올리면 됩니다. 스키마 정의나 SQL 작성 없이 바로 시작할 수 있습니다.",
      tags: ["CSV", "PDF", "XLSX", "DOCX"],
      icon: (
        <svg className="h-6 w-6 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
        </svg>
      ),
    },
    {
      num: "02",
      title: "AI가 구조를 파악",
      desc: "지식 그래프가 자동으로 만들어집니다. FK 관계 추적, 도메인 감지, 벡터 인덱싱까지 — 건드릴 게 없습니다.",
      tags: ["GraphRAG", "도메인 감지", "벡터 인덱스"],
      icon: (
        <svg className="h-6 w-6 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
        </svg>
      ),
    },
    {
      num: "03",
      title: "인사이트 & 실행",
      desc: "매일 자동 브리핑으로 현황을 확인하고, 자연어로 질문해서 근거 있는 답변과 다음 할 일을 받아보세요.",
      tags: ["일일 브리핑", "AI 채팅", "액션 아이템"],
      icon: (
        <svg className="h-6 w-6 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
        </svg>
      ),
    },
  ];

  return (
    <section id="how-it-works">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="pb-12 md:pb-20">
          <div className="mx-auto max-w-2xl pb-12 text-center md:pb-16">
            <h2
              className="text-3xl font-bold text-gray-900 md:text-4xl"
              data-aos="zoom-y-out"
            >
              원시 데이터에서 의사결정까지,{" "}
              <span className="text-amber-500">딱 3단계.</span>
            </h2>
          </div>

          <div className="grid gap-6 md:grid-cols-3" data-aos="zoom-y-out" data-aos-delay={150}>
            {steps.map((step, i) => (
              <div
                key={i}
                className="group relative rounded-2xl border border-gray-200 bg-white p-6 shadow-sm transition-all hover:shadow-md hover:-translate-y-0.5"
              >
                {i < steps.length - 1 && (
                  <div className="absolute -right-3 top-1/2 z-10 hidden -translate-y-1/2 md:block">
                    <div className="flex h-6 w-6 items-center justify-center rounded-full border border-gray-200 bg-white shadow-sm">
                      <svg className="h-3 w-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                )}

                <div className="mb-4 flex items-center justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50 group-hover:bg-amber-100 transition-colors">
                    {step.icon}
                  </div>
                  <span className="font-mono text-3xl font-bold text-gray-100">{step.num}</span>
                </div>

                <h3 className="mb-2 text-lg font-semibold text-gray-900">{step.title}</h3>
                <p className="mb-4 text-sm text-gray-600 leading-relaxed">{step.desc}</p>

                <div className="flex flex-wrap gap-1.5">
                  {step.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full bg-amber-50 px-2.5 py-0.5 text-[11px] font-medium text-amber-600"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
