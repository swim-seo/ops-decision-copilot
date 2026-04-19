import Image from "next/image";
import Stripes from "@/public/images/stripes-dark.svg";

export default function Cta() {
  return (
    <section>
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div
          className="relative overflow-hidden rounded-2xl text-center shadow-xl before:pointer-events-none before:absolute before:inset-0 before:-z-10 before:rounded-2xl before:bg-gray-900"
          data-aos="zoom-y-out"
        >
          <div
            className="absolute bottom-0 left-1/2 -z-10 -translate-x-1/2 translate-y-1/2"
            aria-hidden="true"
          >
            <div className="h-56 w-[480px] rounded-full border-[20px] border-amber-500 blur-3xl" />
          </div>
          <div
            className="pointer-events-none absolute left-1/2 top-0 -z-10 -translate-x-1/2 transform"
            aria-hidden="true"
          >
            <Image className="max-w-none" src={Stripes} width={768} height={432} alt="Stripes" />
          </div>
          <div className="px-4 py-12 md:px-12 md:py-20">
            <h2 className="mb-4 border-y text-3xl font-bold text-gray-200 [border-image:linear-gradient(to_right,transparent,--theme(--color-slate-700/.7),transparent)1] md:mb-8 md:text-4xl">
              추측은 그만, 이제 결정하세요.
            </h2>
            <p className="mb-8 text-gray-400 max-w-xl mx-auto">
              첫 번째 파일을 올리고 3분 안에 운영 현황 전체를 파악해 보세요.
              설정도 SQL도 데이터 팀도 필요 없습니다.
            </p>
            <div className="mx-auto max-w-xs sm:flex sm:max-w-none sm:justify-center gap-3">
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
                className="btn w-full bg-white/10 text-gray-200 hover:bg-white/20 sm:w-auto"
                href="https://github.com/swim-seo/ops-decision-copilot"
                target="_blank"
                rel="noopener noreferrer"
              >
                GitHub 보기
              </a>
            </div>
            <p className="mt-6 text-xs text-gray-500">신용카드 불필요 · 무료 사용 가능 · 엔터프라이즈 문의 환영</p>
          </div>
        </div>
      </div>
    </section>
  );
}
