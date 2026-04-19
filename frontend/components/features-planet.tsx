export default function Features() {
  const features = [
    {
      title: "GraphRAG 지식 엔진",
      desc: "문서를 단순 저장하는 게 아니라, 엔티티와 관계를 추출해 실시간 지식 그래프로 구성합니다. SQL 없이 여러 파일과 테이블을 넘나드는 질문이 가능합니다.",
      icon: "⬡",
      tag: "핵심 기술",
    },
    {
      title: "자동 도메인 감지",
      desc: "파일만 올리면 뷰티, 공급망, 에너지, 제조, 물류, 금융 중 어떤 업종인지 자동으로 파악합니다. 용어와 KPI, 위험 기준까지 도메인에 맞게 조정됩니다.",
      icon: "◎",
      tag: "정확도 90%",
    },
    {
      title: "일일 AI 브리핑",
      desc: "매 세션 자동으로 생성되는 4가지 운영 카드 — 재고 위험, 상위 성과, 발주 필요 항목, 이상 감지. 아무것도 설정할 필요 없습니다.",
      icon: "▦",
      tag: "자동화",
    },
    {
      title: "지능형 데이터 채팅",
      desc: "차트, 순위, 비교, 리스크, 설명 — 5가지 질문 유형을 자동으로 인식해 처리합니다. 답변마다 출처와 다음 할 일이 함께 제공됩니다.",
      icon: "◈",
      tag: "Claude AI",
    },
    {
      title: "범용 파일 수집",
      desc: "CSV, PDF, 엑셀, DOCX 가리지 않습니다. FK 관계를 자동으로 찾아내고 테이블을 연결해, 여러 파일이 하나의 지식층으로 합쳐집니다.",
      icon: "⊞",
      tag: "모든 형식",
    },
    {
      title: "스트리밍 응답",
      desc: "답변이 생성되는 즉시 토큰 단위로 화면에 표시됩니다. 각 응답에는 CSV, 문서, 지식 그래프 중 어디서 왔는지 출처 배지가 붙습니다.",
      icon: "◑",
      tag: "실시간",
    },
  ];

  const domains = [
    { name: "뷰티 / 이커머스", color: "bg-pink-500", text: "Be", desc: "SKU · MOQ · 리드타임 · D2C" },
    { name: "공급망", color: "bg-amber-500", text: "SC", desc: "안전재고 · 발주점 · ABC 분류" },
    { name: "에너지", color: "bg-yellow-500", text: "En", desc: "발전량 · 피크 · 역률" },
    { name: "제조", color: "bg-green-500", text: "Mf", desc: "OEE · 가동률 · 불량률" },
    { name: "물류", color: "bg-purple-500", text: "Lo", desc: "배송율 · 노선 · 차량" },
    { name: "금융", color: "bg-cyan-500", text: "Fi", desc: "신용등급 · 리스크 · 이상거래" },
  ];

  return (
    <>
      <section id="features" className="relative before:absolute before:inset-0 before:-z-20 before:bg-slate-900">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="py-12 md:py-20">
            <div className="mx-auto max-w-3xl pb-12 text-center md:pb-16">
              <h2
                className="text-3xl font-bold text-gray-200 md:text-4xl"
                data-aos="zoom-y-out"
              >
                운영팀에{" "}
                <span className="text-amber-400">실제로 필요한 기능들.</span>
              </h2>
              <p className="mt-4 text-gray-400" data-aos="zoom-y-out" data-aos-delay={100}>
                공급망, 제조, 재무 담당자를 위해 만든 도구입니다.
                또 하나의 BI 툴이 아니라, 빠른 답이 필요한 사람을 위한 코파일럿입니다.
              </p>
            </div>

            <div
              className="grid overflow-hidden sm:grid-cols-2 lg:grid-cols-3 *:relative *:p-6 *:before:absolute *:before:bg-gray-800 *:before:[block-size:100vh] *:before:[inline-size:1px] *:before:[inset-block-start:0] *:before:[inset-inline-start:-1px] *:after:absolute *:after:bg-gray-800 *:after:[block-size:1px] *:after:[inline-size:100vw] *:after:[inset-block-start:-1px] *:after:[inset-inline-start:0] md:*:p-8"
              data-aos="zoom-y-out"
              data-aos-delay={150}
            >
              {features.map((feat, i) => (
                <article key={i} className="group">
                  <div className="mb-3 flex items-center gap-3">
                    <span className="text-2xl text-amber-400 group-hover:text-amber-300 transition-colors">
                      {feat.icon}
                    </span>
                    <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-amber-400">
                      {feat.tag}
                    </span>
                  </div>
                  <h3 className="mb-1 font-semibold text-gray-200">{feat.title}</h3>
                  <p className="text-[14px] text-gray-400 leading-relaxed">{feat.desc}</p>
                </article>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="domains">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="py-12 md:py-20">
            <div className="mx-auto max-w-3xl pb-12 text-center md:pb-16">
              <h2
                className="text-3xl font-bold text-gray-900 md:text-4xl"
                data-aos="zoom-y-out"
              >
                우리 업종에 맞게,{" "}
                <span className="text-amber-500">설치 없이 바로.</span>
              </h2>
              <p className="mt-4 text-gray-600" data-aos="zoom-y-out" data-aos-delay={100}>
                7개 산업 프리셋이 기본 탑재되어 있습니다. 없는 도메인은 이름만 입력하면 Claude가 바로 설정을 만들어 줍니다.
              </p>
            </div>

            <div
              className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
              data-aos="zoom-y-out"
              data-aos-delay={150}
            >
              {domains.map((d, i) => (
                <div
                  key={i}
                  className="flex items-center gap-4 rounded-xl border border-gray-200 bg-white p-4 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all"
                >
                  <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${d.color} text-white text-sm font-bold`}>
                    {d.text}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900 text-sm">{d.name}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{d.desc}</p>
                  </div>
                </div>
              ))}

              <div className="flex items-center gap-4 rounded-xl border border-dashed border-gray-300 bg-gray-50 p-4 hover:border-amber-300 hover:bg-amber-50 transition-all cursor-pointer">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border-2 border-dashed border-gray-300 text-gray-400 text-lg hover:border-amber-400 hover:text-amber-500 transition-colors">
                  +
                </div>
                <div>
                  <p className="font-semibold text-gray-600 text-sm">커스텀 도메인</p>
                  <p className="text-xs text-gray-400 mt-0.5">이름만 입력하면 Claude가 즉시 생성</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
