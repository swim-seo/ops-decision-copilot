export const metadata = {
  title: "기능 — Ops Copilot",
  description: "운영팀에 실제로 필요한 것들. GraphRAG, 도메인 감지, 일일 브리핑 등 핵심 기능을 상세히 소개합니다.",
};

const features = [
  {
    icon: "⬡",
    tag: "핵심 기술",
    title: "GraphRAG 지식 엔진",
    desc: "Ops Copilot은 문서를 단순히 저장하지 않습니다. 문서에서 실시간 지식 그래프를 자동으로 구성합니다. 엔티티와 관계가 자동으로 추출되고 연결되며, 멀티홉 추론으로 여러 파일과 테이블에 걸친 질문에도 SQL 없이 답할 수 있습니다.",
    bullets: [
      "Claude를 통한 자동 엔티티 & 관계 추출",
      "CSV 테이블 간 FK 체인 추적",
      "3단계 드릴다운 노드 그래프 시각화",
      "커뮤니티 감지를 통한 클러스터 요약",
    ],
  },
  {
    icon: "◎",
    tag: "90% 정확도",
    title: "자동 도메인 감지",
    desc: "파일을 업로드하면 Ops Copilot이 업종 맥락을 자동으로 파악합니다 — 뷰티, 공급망, 에너지, 제조, 물류, 금융. 분석 파이프라인 전체가 해당 도메인의 용어, KPI, 위험 임계값에 맞춰 자동 조정됩니다.",
    bullets: [
      "7개 기본 도메인 프리셋",
      "Claude 생성 설정으로 커스텀 도메인 지원",
      "모든 프롬프트에 도메인 전용 용어 자동 주입",
      "20개 테스트 케이스 기준 90% 감지 정확도",
    ],
  },
  {
    icon: "▦",
    tag: "자동화",
    title: "일일 AI 브리핑",
    desc: "매 세션 시작 시 Claude가 4카드 운영 현황을 자동으로 생성합니다. 설정 없이, 대시보드 없이. 재고 경보, 상위 성과, 발주 트리거, 이상 감지 — 업로드한 데이터에서 자동으로 추출됩니다.",
    bullets: [
      "재고 위험 카드 — 안전재고 미달 SKU",
      "상위 성과 카드 — 채널별 베스트셀러",
      "발주 트리거 카드 — 오늘 액션이 필요한 항목",
      "이상 감지 카드 — 리드타임 편차 및 이상값",
    ],
  },
  {
    icon: "◈",
    tag: "Claude AI",
    title: "지능형 데이터 채팅",
    desc: "자연어로 질문하면 됩니다. Ops Copilot이 쿼리 유형을 자동으로 분류해 적합한 분석 엔진으로 라우팅합니다. 모든 답변에는 출처 인용과 다음 액션 권고가 포함됩니다.",
    bullets: [
      "차트 — 특정 SKU의 시계열 및 막대 차트",
      "순위 — 상위/하위 성과, 계절성 포함",
      "비교 — 전년 대비, 채널 간 비교",
      "리스크 — 품절 커버리지 및 발주 긴급도",
      "설명 — RAG + KG 결합 서술형 답변",
    ],
  },
  {
    icon: "⊞",
    tag: "모든 형식",
    title: "범용 데이터 수집",
    desc: "어떤 파일 조합이든 업로드하세요. CSV 테이블은 스키마가 분석되고 FK 관계가 자동 감지됩니다. PDF와 DOCX는 파싱되고 청킹되어 시맨틱 인덱싱됩니다. 모든 파일이 하나의 통합 지식 레이어로 연결됩니다.",
    bullets: [
      "CSV — 컬럼 타입 분석, FK 후보 감지, 테이블 연결",
      "PDF — 전문 추출 및 시맨틱 청킹",
      "DOCX / TXT / MD — 문서 파싱 및 인덱싱",
      "중복 제거 — 재업로드 시 기존 청크 교체",
    ],
  },
  {
    icon: "◑",
    tag: "실시간",
    title: "스트리밍 응답",
    desc: "Claude의 답변이 토큰 단위로 실시간 스트리밍되어 생성되는 즉시 읽을 수 있습니다. 모든 응답에는 출처 배지 — CSV 데이터, RAG 문서, 또는 지식 그래프 노드 — 가 태그됩니다.",
    bullets: [
      "Anthropic SDK를 통한 실시간 토큰 스트리밍",
      "출처 배지: CSV / 문서 / 지식 그래프",
      "모든 답변에 다음 액션 섹션 자동 추가",
      "API 안정성을 위한 지수 백오프 재시도",
    ],
  },
];

export default function FeaturesPage() {
  return (
    <section className="relative">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="pb-12 pt-32 md:pb-20 md:pt-40">

          <div className="mx-auto max-w-3xl pb-16 text-center">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-amber-100 bg-amber-50 px-4 py-1.5 text-sm font-medium text-amber-600">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse" />
              기능 상세
            </div>
            <h1 className="mb-4 text-4xl font-bold text-gray-900 md:text-5xl">
              운영팀에{" "}
              <span className="text-amber-500">실제로 필요한 것들.</span>
            </h1>
            <p className="text-lg text-gray-600">
              공급망 담당자, 제조 운영팀, 재무팀을 위해 만들었습니다.
              유지보수가 필요한 BI 툴 대신, 빠른 답변을 드립니다.
            </p>
          </div>

          <div className="space-y-8">
            {features.map((feat, i) => (
              <div
                key={i}
                className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm"
                data-aos="zoom-y-out"
                data-aos-delay={i * 50}
              >
                <div className="grid gap-8 md:grid-cols-2 md:items-start">
                  <div>
                    <div className="mb-3 flex items-center gap-3">
                      <span className="text-2xl text-amber-500">{feat.icon}</span>
                      <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-amber-600">
                        {feat.tag}
                      </span>
                    </div>
                    <h2 className="mb-3 text-xl font-bold text-gray-900">{feat.title}</h2>
                    <p className="text-gray-600 leading-relaxed">{feat.desc}</p>
                  </div>
                  <ul className="space-y-2.5">
                    {feat.bullets.map((b, j) => (
                      <li key={j} className="flex items-start gap-2.5 text-sm text-gray-700">
                        <svg className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                        {b}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-16 text-center">
            <a
              href="/app"className="btn bg-linear-to-t from-amber-600 to-amber-500 bg-[length:100%_100%] bg-[bottom] text-white shadow-sm hover:bg-[length:100%_150%]"
            >
              모든 기능 직접 사용해보기 →
            </a>
          </div>

        </div>
      </div>
    </section>
  );
}
