export const metadata = {
  title: "도메인 — Ops Copilot",
  description: "7개 산업 프리셋 기본 제공. 도메인 이름만 입력하면 Claude가 맞춤 설정을 즉시 생성합니다.",
};

const domains = [
  {
    abbr: "Be",
    color: "bg-pink-500",
    border: "border-pink-200",
    accent: "text-pink-600 bg-pink-50",
    name: "뷰티 / 이커머스",
    desc: "SKU, 채널, 공급업체 관계를 관리하는 뷰티 브랜드를 위해 설계됐습니다. MOQ, 리드타임, D2C vs 도매 비율, 계절 수요 급등을 추적합니다.",
    metrics: ["SKU 커버리지율", "MOQ 준수율", "D2C vs 도매 비율", "리드타임 편차"],
    questions: [
      "성수기 전 안전재고 미달 SKU는?",
      "Q1 vs Q2 D2C 대 도매 매출 비교",
      "이번 달 리드타임 편차가 가장 큰 공급업체는?",
    ],
    formats: ["상품 마스터 CSV", "채널별 매출 CSV", "공급업체 리드타임 리포트"],
  },
  {
    abbr: "SC",
    color: "bg-amber-500",
    border: "border-amber-200",
    accent: "text-amber-600 bg-amber-50",
    name: "공급망",
    desc: "재고, 조달, 풀필먼트 전반의 공급망 가시성. ABC 분류, 발주 트리거, 공급업체 성과 모니터링.",
    metrics: ["안전재고 커버리지", "발주점", "ABC 분류", "충족률"],
    questions: [
      "이번 주 재발주가 필요한 A등급 품목은?",
      "전체 SKU의 재고 커버리지 일수 표시",
      "납기 준수율로 공급업체 순위 매기기",
    ],
    formats: ["재고 스냅샷 CSV", "발주서 CSV", "공급업체 스코어카드"],
  },
  {
    abbr: "En",
    color: "bg-yellow-500",
    border: "border-yellow-200",
    accent: "text-yellow-700 bg-yellow-50",
    name: "에너지",
    desc: "발전, 소비, 그리드 운영 모니터링. 피크 수요, 역률, 신재생 에너지 비율, 에너지 흐름 이상을 추적합니다.",
    metrics: ["발전량 vs 소비량", "피크 수요", "역률", "신재생 비율 %"],
    questions: [
      "이번 주 피크 수요가 임계값을 초과한 시점은?",
      "역률 점수가 가장 낮은 사이트는?",
      "최근 30일 신재생 vs 화석연료 발전 요약",
    ],
    formats: ["시간별 발전량 CSV", "사이트 소비 리포트", "그리드 이상 로그"],
  },
  {
    abbr: "Mf",
    color: "bg-green-500",
    border: "border-green-200",
    accent: "text-green-600 bg-green-50",
    name: "제조",
    desc: "생산 라인의 OEE, 가동률, 품질 관리. 불량률 급등, 다운타임 패턴, 생산 병목 감지.",
    metrics: ["OEE", "가동률", "불량률", "비계획 다운타임"],
    questions: [
      "이번 주 OEE가 가장 낮은 생산 라인은?",
      "라인 3의 30일간 불량률 추이",
      "지난달 비계획 다운타임의 주요 원인은?",
    ],
    formats: ["생산 로그 CSV", "품질 관리 리포트", "설비 유지보수 기록"],
  },
  {
    abbr: "Lo",
    color: "bg-purple-500",
    border: "border-purple-200",
    accent: "text-purple-600 bg-purple-50",
    name: "물류",
    desc: "차량, 노선, 배송 성과 추적. 정시 배송률, 노선 효율성, 물류 네트워크 전반의 운송비 분석.",
    metrics: ["정시 배송률", "노선 효율성", "운송비/km", "파손율"],
    questions: [
      "정시 배송률이 가장 낮은 노선은?",
      "지역별 운송사 비용 비교",
      "지난 분기 운송사별 파손 화물 추이",
    ],
    formats: ["배송 추적 CSV", "노선 성과 데이터", "운송사 청구서 내보내기"],
  },
  {
    abbr: "Fi",
    color: "bg-cyan-500",
    border: "border-cyan-200",
    accent: "text-cyan-700 bg-cyan-50",
    name: "금융",
    desc: "재무 운영팀을 위한 신용 리스크, 이상 감지, 포트폴리오 모니터링. 고위험 계정, 비정상 거래, 조건 위반을 플래그합니다.",
    metrics: ["신용등급 분포", "매출채권 회수일수(DSO)", "리스크 익스포저", "이상 감지율"],
    questions: [
      "연체 위험이 가장 높은 계정은?",
      "기준선 대비 2σ 이상 편차 거래 플래그",
      "최근 6개월 고객 세그먼트별 DSO 추이",
    ],
    formats: ["매출채권 연령 분석 CSV", "거래 이력 CSV", "신용 평가 리포트"],
  },
  {
    abbr: "G",
    color: "bg-slate-500",
    border: "border-slate-200",
    accent: "text-slate-600 bg-slate-50",
    name: "커스텀 도메인",
    desc: "원하는 업종이 없나요? 업종 이름을 입력하면 Claude가 엔티티 타입, 용어, KPI, 분석 방향을 포함한 도메인 설정을 즉시 생성합니다. 코드 불필요.",
    metrics: ["자동 생성 KPI", "도메인별 엔티티", "맞춤 용어", "적응형 프롬프트"],
    questions: [
      "해당 도메인의 모든 운영 질문 가능",
      "Claude가 업로드한 파일 기반으로 적응",
      "프리셋 없이도 맥락만 설명하면 됨",
    ],
    formats: ["CSV, PDF, DOCX, TXT 등 모든 형식"],
  },
];

export default function DomainsPage() {
  return (
    <section className="relative">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="pb-12 pt-32 md:pb-20 md:pt-40">

          <div className="mx-auto max-w-3xl pb-16 text-center">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-amber-100 bg-amber-50 px-4 py-1.5 text-sm font-medium text-amber-600">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse" />
              7개 도메인 + 커스텀
            </div>
            <h1 className="mb-4 text-4xl font-bold text-gray-900 md:text-5xl">
              우리 업종에 맞게,{" "}
              <span className="text-amber-500">바로 사용 가능.</span>
            </h1>
            <p className="text-lg text-gray-600">
              각 도메인 프리셋은 용어, KPI, 분석 로직을 자동으로 조정합니다.
              도메인 이름만 입력하면 Claude가 맞춤 설정을 즉시 생성합니다.
            </p>
          </div>

          <div className="space-y-6">
            {domains.map((d, i) => (
              <div
                key={i}
                className={`rounded-2xl border ${d.border} bg-white p-8 shadow-sm`}
                data-aos="zoom-y-out"
                data-aos-delay={i * 50}
              >
                <div className="grid gap-8 md:grid-cols-3">
                  <div>
                    <div className="mb-4 flex items-center gap-3">
                      <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${d.color} text-sm font-bold text-white`}>
                        {d.abbr}
                      </div>
                      <h2 className="text-lg font-bold text-gray-900">{d.name}</h2>
                    </div>
                    <p className="text-sm text-gray-600 leading-relaxed">{d.desc}</p>
                    <div className="mt-4 flex flex-wrap gap-1.5">
                      {d.formats.map((f) => (
                        <span key={f} className={`rounded-full px-2.5 py-0.5 text-[11px] font-medium ${d.accent}`}>
                          {f}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div>
                    <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-400">핵심 지표</p>
                    <ul className="space-y-2">
                      {d.metrics.map((m) => (
                        <li key={m} className="flex items-center gap-2 text-sm text-gray-700">
                          <span className={`h-1.5 w-1.5 rounded-full ${d.color}`} />
                          {m}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-400">샘플 질문</p>
                    <ul className="space-y-2.5">
                      {d.questions.map((q) => (
                        <li key={q} className="rounded-lg bg-gray-50 px-3 py-2 text-xs text-gray-600 leading-relaxed">
                          "{q}"
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-16 text-center">
            <a
              href="/app"className="btn bg-linear-to-t from-amber-600 to-amber-500 bg-[length:100%_100%] bg-[bottom] text-white shadow-sm hover:bg-[length:100%_150%]"
            >
              내 도메인으로 시작하기 →
            </a>
          </div>

        </div>
      </div>
    </section>
  );
}
