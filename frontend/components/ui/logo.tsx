import Link from "next/link";

export default function Logo() {
  return (
    <Link href="/" className="inline-flex items-center gap-2" aria-label="Ops Copilot">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none">
        <polygon points="12,2 22,7 22,17 12,22 2,17 2,7" className="fill-amber-500" />
        <polygon points="12,6 18,9.5 18,16.5 12,20 6,16.5 6,9.5" fill="white" opacity="0.3" />
      </svg>
      <span className="font-semibold text-gray-900 text-[15px] tracking-tight">
        Ops<span className="text-amber-500">.</span>Copilot
      </span>
    </Link>
  );
}
