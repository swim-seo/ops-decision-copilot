export const metadata = {
  title: "가이드 — Ops Copilot",
  description: "Ops Copilot 시작하기. 데이터 업로드부터 지식 그래프 탐색, 질문까지 3분이면 충분합니다.",
};

const steps = [
  {
    num: "01",
    title: "도메인 선택",
    desc: "7개 산업 프리셋 중 하나를 선택하거나 도메인 이름을 직접 입력하세요. Ops Copilot이 이를 기반으로 용어, KPI, 위험 임계값을 자동으로 조정합니다.",
    tips: [
      "프리셋: 뷰티, 공급망, 에너지, 제조, 물류, 금융, 일반",
      "커스텀 도메인: 이름만 입력하면 Claude가 하나의 API 호출로 설정 생성",
      "도메인은 언제든 변경 가능 — 각 도메인은 별도 벡터 저장소 사용",
    ],
    note: null,
  },
  {
    num: "02",
    title: "파일 업로드",
    desc: "CSV, PDF, 엑셀, DOCX, TXT 파일을 자유롭게 조합해 업로드하세요. 샘플 데이터셋을 먼저 불러와 시스템을 탐색해볼 수도 있습니다.",
    tips: [
      "CSV — 스키마 분석, FK 관계 자동 감지, 테이블 연결",
      "PDF / DOCX — 파싱, 청킹(500토큰, 50 오버랩), 시맨틱 인덱싱",
      "여러 파일 — 병렬 처리, 지식 그래프 점진적 구성",
      "재업로드 — 기존 청크 교체 (중복 없음)",
    ],
    note: "FK 자동 감지가 누락된 관계가 있을 경우 SCHEMA_DEFINITION.json 형식으로 테이블 관계를 명시할 수 있습니다.",
  },
  {
    num: "03",
    title: "지식 그래프 탐색",
    desc: "업로드 후 KG 탭에서 데이터를 3가지 뷰로 확인하세요. 질문하기 전에 Ops Copilot이 무엇을 학습했는지 먼저 파악하세요.",
    tips: [
      "노드 그래프 — 노드 클릭으로 레벨 2 이웃, 레벨 3까지 드릴다운",
      "ERD 테이블 뷰 — 업로드된 CSV 테이블의 카드형 스키마 표시",
      "데이터 흐름 뷰 — MST 기반 소스 테이블에서 FACT 테이블로의 방향성 흐름",
    ],
    note: null,
  },
  {
    num: "04",
    title: "일일 브리핑 받기",
    desc: "AI 분석 탭에서 브리핑 생성 버튼을 누르면 Claude가 업로드된 파일에서 4카드 현황을 자동 생성합니다. 별도 설정 없이 바로 사용하세요.",
    tips: [
      "재고 위험 — 안전재고 임계값 미달 SKU 또는 항목",
      "상위 성과 — 베스트셀러 상품 또는 최고 출력 엔티티",
      "발주 트리거 — 오늘 구매 조치가 필요한 항목",
      "이상 감지 — 리드타임, 물량, 비용의 통계적 이상값",
    ],
    note: "데모 세션은 API 호출 20회로 제한됩니다. 브리핑은 카드당 1회, 총 4회를 사용합니다.",
  },
  {
    num: "05",
    title: "채팅으로 질문하기",
    desc: "채팅 탭에서 운영 관련 질문을 자연어로 입력하세요. Ops Copilot이 쿼리 유형을 자동 감지해 적합한 엔진으로 라우팅합니다. 모든 답변에는 출처 태그와 다음 액션 권고가 포함됩니다.",
    tips: [
      "차트: 제품 코드(예: FG-001) 언급 또는 '차트로 보여줘'",
      "순위: '상위 5개', '베스트셀러', '순위 매겨줘'",
      "비교: '비교해줘', 'vs', '전년 대비'",
      "리스크: '품절 위험', '긴급', '발주 필요'",
      "그 외: 자연어로 질문 — RAG + KG 결합 답변",
    ],
    note: null,
  },
];

const faq = [
  {
    q: "파일 크기 제한이 있나요?",
    a: "앱에서 별도로 제한을 두지는 않습니다. 다만 매우 큰 CSV 파일(10만 행 이상)은 pandas 연산이 느려질 수 있습니다. PDF는 페이지 수에 관계없이 전체 파싱됩니다.",
  },
  {
    q: "세션 간에 데이터가 유지되나요?",
    a: "ChromaDB 벡터 저장소는 같은 머신에서 세션 간 유지됩니다. 지식 그래프 HTML은 매 세션 재생성됩니다. Streamlit Cloud에서는 배포마다 초기화됩니다.",
  },
  {
    q: "내 Claude API 키를 사용할 수 있나요?",
    a: "가능합니다 — .env 파일 또는 Streamlit secret에 ANTHROPIC_API_KEY를 설정하세요. 앱은 st.secrets → .env → 환경변수 순으로 키를 확인합니다.",
  },
  {
    q: "도메인 감지는 어떻게 작동하나요?",
    a: "도메인 이름이 7개 기본 프리셋 중 하나와 키워드 매칭되면 해당 프리셋 설정이 사용됩니다. 그 외의 경우 Claude API 호출 한 번으로 도메인 이름을 분석해 커스텀 DomainConfig JSON을 반환합니다.",
  },
  {
    q: "어떤 AI 모델을 사용하나요?",
    a: "모든 AI 호출은 claude-sonnet-4-5 (또는 config.py에서 설정한 모델)를 사용합니다. 임베딩은 sentence-transformers paraphrase-multilingual-MiniLM-L12-v2를 로컬에서 실행합니다.",
  },
];

export default function GuidePage() {
  return (
    <section className="relative">
      <div className="mx-auto max-w-4xl px-4 sm:px-6">
        <div className="pb-12 pt-32 md:pb-20 md:pt-40">

          <div className="pb-16 text-center">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-amber-100 bg-amber-50 px-4 py-1.5 text-sm font-medium text-amber-600">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse" />
              시작하기
            </div>
            <h1 className="mb-4 text-4xl font-bold text-gray-900 md:text-5xl">
              3분이면{" "}
              <span className="text-amber-500">바로 시작됩니다.</span>
            </h1>
            <p className="text-lg text-gray-600">
              SQL 없이. 스키마 설정 없이. 데이터 팀 없이.
            </p>
          </div>

          <div className="space-y-6">
            {steps.map((step, i) => (
              <div
                key={i}
                className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm"
                data-aos="zoom-y-out"
                data-aos-delay={i * 50}
              >
                <div className="mb-4 flex items-center gap-4">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-500 text-sm font-bold text-white">
                    {step.num}
                  </span>
                  <h2 className="text-xl font-bold text-gray-900">{step.title}</h2>
                </div>
                <p className="mb-4 text-gray-600 leading-relaxed">{step.desc}</p>
                <ul className="space-y-2">
                  {step.tips.map((tip, j) => (
                    <li key={j} className="flex items-start gap-2.5 text-sm text-gray-700">
                      <svg className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      {tip}
                    </li>
                  ))}
                </ul>
                {step.note && (
                  <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                    <span className="font-semibold">참고: </span>{step.note}
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="mt-16">
            <h2 className="mb-8 text-2xl font-bold text-gray-900">자주 묻는 질문</h2>
            <div className="space-y-4">
              {faq.map((item, i) => (
                <div key={i} className="rounded-xl border border-gray-200 bg-white p-6">
                  <p className="mb-2 font-semibold text-gray-900">{item.q}</p>
                  <p className="text-sm text-gray-600 leading-relaxed">{item.a}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-16 text-center">
            <a
              href="/app"className="btn bg-linear-to-t from-amber-600 to-amber-500 bg-[length:100%_100%] bg-[bottom] text-white shadow-sm hover:bg-[length:100%_150%]"
            >
              앱 열기 →
            </a>
          </div>

        </div>
      </div>
    </section>
  );
}
