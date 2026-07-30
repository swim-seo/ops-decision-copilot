import "./css/style.css";

import { Inter, Hahmlet, IBM_Plex_Sans_KR, IBM_Plex_Mono } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

// next/font 메타데이터에는 이 폰트들의 korean 서브셋이 없다. subsets:["latin"] 로
// 받으면 한글 글리프가 빠져 시스템 폰트로 조용히 떨어지므로, subsets 를 생략하고
// preload:false 로 전 유니코드 범위를 self-host 한다.
const hahmlet = Hahmlet({
  weight: ["500", "700"],
  variable: "--ff-display",
  display: "swap",
  preload: false,
});

const plexSansKr = IBM_Plex_Sans_KR({
  weight: ["400", "500", "600"],
  variable: "--ff-ui",
  display: "swap",
  preload: false,
});

// 데이터용 — 테이블명·FK·수치는 ASCII 뿐이라 latin 서브셋으로 충분하다.
const plexMono = IBM_Plex_Mono({
  weight: ["400", "500"],
  subsets: ["latin"],
  variable: "--ff-data",
  display: "swap",
});

export const metadata = {
  title: "Ops Decision Copilot — AI Operational Intelligence",
  description:
    "Upload your operational data. Get instant AI analysis, knowledge graphs, and actionable decisions. Built for enterprise operations teams.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <body
        className={`${inter.variable} ${hahmlet.variable} ${plexSansKr.variable} ${plexMono.variable} bg-gray-50 font-inter tracking-tight text-gray-900 antialiased`}
      >
        <div className="flex min-h-screen flex-col overflow-hidden supports-[overflow:clip]:overflow-clip">
          {children}
        </div>
      </body>
    </html>
  );
}
