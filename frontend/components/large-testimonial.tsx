export default function Stats() {
  const stats = [
    { value: "90%", label: "도메인 감지 정확도", sub: "20개 테스트 중 18개 적중" },
    { value: "100%", label: "FK 감지 정밀도", sub: "오탐지 0건" },
    { value: "7+", label: "지원 산업 도메인", sub: "커스텀 도메인 포함" },
    { value: "<3초", label: "첫 인사이트까지", sub: "업로드 후 답변 시작" },
  ];

  return (
    <section>
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="py-12 md:py-20">
          <div
            className="grid grid-cols-2 gap-6 lg:grid-cols-4"
            data-aos="zoom-y-out"
          >
            {stats.map((s, i) => (
              <div key={i} className="text-center">
                <div className="text-4xl font-bold text-amber-600 md:text-5xl">{s.value}</div>
                <p className="mt-1 font-semibold text-gray-900 text-sm">{s.label}</p>
                <p className="text-xs text-gray-500 mt-0.5">{s.sub}</p>
              </div>
            ))}
          </div>

          <div className="my-12 border-t border-gray-200" />

          <div className="mx-auto max-w-2xl text-center" data-aos="zoom-y-out" data-aos-delay={150}>
            <p className="text-2xl font-bold text-gray-900">
              &ldquo;매일 아침 리포트 만드는 데 2시간을 썼는데,
              이제는{" "}
              <em className="italic text-gray-500">노트북 열기 전에 Ops Copilot 브리핑이 먼저 와 있습니다.</em>&rdquo;
            </p>
            <div className="mt-4 text-sm font-medium text-gray-500">
              <span className="text-gray-700">운영 총괄</span>{" "}
              <span className="text-gray-400">/</span>{" "}
              <span className="text-amber-500">뷰티 브랜드, 연매출 500억</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
