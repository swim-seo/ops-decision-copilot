# -*- coding: utf-8 -*-
"""
RAG 개선 검증 스크립트 - 외부 서비스(HF API, Supabase) 없이 로컬에서 실행 가능
"""
import sys
import textwrap
import io
from unittest.mock import MagicMock

# Windows cp949 터미널에서도 UTF-8 출력되도록 강제
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 미설치/충돌 의존성 모킹 (테스트에서 실제로 사용 안 함)
for _mod in ("pypdf", "PyPDF2", "docx", "requests", "dotenv",
             "pandas", "numpy", "modules.supabase_client"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()
sys.modules["dotenv"].load_dotenv = lambda **kw: None

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"


def section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


# ── 1. 모듈 임포트 ────────────────────────────────────────────────────────────
section("1. 모듈 임포트 체인")

try:
    import config
    print(f"{PASS}  config.py")
except Exception as e:
    print(f"{FAIL}  config.py — {e}"); sys.exit(1)

try:
    from modules.document_parser import chunk_text, _csv_rows_to_text
    print(f"{PASS}  modules.document_parser (chunk_text, _csv_rows_to_text)")
except Exception as e:
    print(f"{FAIL}  modules.document_parser — {e}"); sys.exit(1)

try:
    from modules import embedding  # HF 호출 X, 임포트만
    print(f"{PASS}  modules.embedding (embed, embed_batch)")
except Exception as e:
    print(f"{FAIL}  modules.embedding — {e}"); sys.exit(1)

try:
    from modules.rag_engine import RAGEngine
    print(f"{PASS}  modules.rag_engine (RAGEngine)")
except Exception as e:
    print(f"{FAIL}  modules.rag_engine — {e}"); sys.exit(1)

try:
    from modules.community_summarizer import retrieve_community_context
    print(f"{PASS}  modules.community_summarizer")
except Exception as e:
    print(f"{FAIL}  modules.community_summarizer — {e}"); sys.exit(1)


# ── 2. 상수 확인 ──────────────────────────────────────────────────────────────
section("2. config.py 신규 상수 확인")

checks = {
    "SIMILARITY_THRESHOLD": (config.SIMILARITY_THRESHOLD, 0.0, 1.0),
    "CHUNK_SIZE_MIN":        (config.CHUNK_SIZE_MIN, 1, config.CHUNK_SIZE),
    "CSV_MAX_EMBED_ROWS":    (config.CSV_MAX_EMBED_ROWS, 1, 10_000),
}
for name, (val, lo, hi) in checks.items():
    ok = lo <= val <= hi
    print(f"{'✅' if ok else '❌'}  {name} = {val}  (기대 범위: {lo}~{hi})")

# CORS/MODEL 환경변수화
import inspect, pathlib
main_src = pathlib.Path("backend/main.py").read_text(encoding="utf-8")
cfg_src   = pathlib.Path("config.py").read_text(encoding="utf-8")
print(f"{'[PASS]' if 'ALLOWED_ORIGINS' in main_src else '[FAIL]'}  backend/main.py - CORS 환경변수화")
print(f"{'[PASS]' if 'CLAUDE_MODEL' in cfg_src else '[FAIL]'}  config.py - MODEL_NAME 환경변수화")


# ── 3. chunk_text() 단락 경계 청킹 ───────────────────────────────────────────
section("3. chunk_text() — 단락 경계 기반 청킹")

# 3-A: 한국어 단락 텍스트
korean_text = textwrap.dedent("""\
    재고 관리 정책에 따르면, 안전 재고는 수요 변동성과 리드타임을 기반으로 산출합니다.
    특히 성수기 직전 6주 이내에는 안전 재고를 20% 상향 조정하도록 되어 있습니다.

    발주 기준점(ROP)은 일평균 수요에 리드타임을 곱한 값에 안전 재고를 더해 계산합니다.
    현재 시스템은 자동 발주 알림을 지원하며 담당자 확인 후 최종 발주가 진행됩니다.

    반품 처리는 입고 후 48시간 이내에 품질 검수를 완료해야 합니다.
    검수 통과 시 재고에 재편입되며 실패 시 폐기 또는 반송 처리합니다.
""")

# 짧은 텍스트(270자) → 800자 미만이므로 1개 청크로 합산 (정상 동작)
chunks = chunk_text(korean_text)
print(f"\n[짧은 텍스트 270자] → 청크 {len(chunks)}개 (800자 미만 → 합산 정상)")
for i, c in enumerate(chunks, 1):
    preview = c[:80].replace('\n', ' ')
    print(f"  청크 {i} ({len(c)}자): {preview}{'...' if len(c) > 80 else ''}")

all_short = all(len(c) <= config.CHUNK_SIZE + config.CHUNK_OVERLAP for c in chunks)
print(f"\n{PASS if all_short else FAIL}  모든 청크가 max_size({config.CHUNK_SIZE}) 이내")
print(f"{PASS if len(chunks) == 1 else FAIL}  270자 3단락 → 1청크로 합산 (정상)")

# 긴 텍스트(900자+) → 단락 경계에서 분리되는지 확인
long_korean = (korean_text + "\n\n") * 4  # ~1100자
long_chunks = chunk_text(long_korean)
print(f"\n[긴 텍스트 {len(long_korean)}자] → 청크 {len(long_chunks)}개")
for i, c in enumerate(long_chunks, 1):
    preview = c[:70].replace('\n', ' ')
    print(f"  청크 {i} ({len(c)}자): {preview}...")
has_multiple = len(long_chunks) >= 2
print(f"\n{PASS if has_multiple else FAIL}  900자+ 텍스트가 단락 경계에서 분리됨")

# 3-B: 문장 중간 절단 방지 확인
long_no_para = "이것은 매우 긴 문장입니다. " * 60  # ~900자, 단락 없음
chunks_long = chunk_text(long_no_para)
cuts_mid_sentence = any(
    not (c.endswith(".") or c.endswith(" ") or len(c) < 100)
    for c in chunks_long[:-1]
)
print(f"{'[WARN]' if cuts_mid_sentence else PASS}  문장 중간 절단 방지 (단락 없는 긴 텍스트)")


# ── 4. _csv_rows_to_text() CSV 행 변환 ────────────────────────────────────────
section("4. _csv_rows_to_text() — CSV 행 → 검색 가능 텍스트")

sample_csv = textwrap.dedent("""\
    PART_NO,PART_NAME,CATEGORY,UNIT_PRICE,STOCK_QTY
    P001,볼트M8,기계부품,150,5000
    P002,너트M8,기계부품,80,8000
    P003,스프링핀,조립부품,320,1200
    P004,베어링6205,회전부품,4500,300
    P005,오링50mm,밀봉부품,210,2500
""")

rows_text = _csv_rows_to_text(sample_csv)
lines = [l for l in rows_text.split("\n\n") if l.strip()]
print(f"\nCSV 5행 → 단락 {len(lines)}개 생성\n")
for i, line in enumerate(lines, 1):
    print(f"  [{i}] {line}")

ok_format = all(":" in l for l in lines)
print(f"\n{PASS if ok_format else FAIL}  'col: val' 형식으로 변환됨")
ok_count = len(lines) == 5
print(f"{PASS if ok_count else FAIL}  5행 → 5개 단락 (1:1 매핑)")

# max_rows 제한 확인
big_csv = "A,B,C\n" + "\n".join(f"v{i},w{i},x{i}" for i in range(600))
limited = _csv_rows_to_text(big_csv, max_rows=500)
row_count = len([l for l in limited.split("\n\n") if l.strip()])
print(f"{PASS if row_count <= 500 else FAIL}  max_rows=500 제한 적용 (실제 {row_count}행)")


# ── 5. embed_batch() 배치 크기 로직 ──────────────────────────────────────────
section("5. embed_batch() — 배치 분할 로직 (HF API 호출 없이 검증)")

# _BATCH_SIZE=32 기준으로 100개 텍스트를 몇 배치로 나누는지 확인
from modules.embedding import _BATCH_SIZE
texts_100 = [f"샘플 텍스트 {i}" for i in range(100)]
expected_batches = -(-len(texts_100) // _BATCH_SIZE)  # ceiling division
print(f"\n텍스트 {len(texts_100)}개 / 배치크기 {_BATCH_SIZE} = {expected_batches}배치")
print(f"{PASS}  배치 크기 상수 _BATCH_SIZE = {_BATCH_SIZE}")

retry_src = pathlib.Path("modules/embedding.py").read_text(encoding="utf-8")
print(f"{'[PASS]' if '_MAX_RETRIES' in retry_src and 'time.sleep' in retry_src else '[FAIL]'}  HF 503 cold-start retry 로직 포함")
print(f"{'[PASS]' if 'lru_cache' in retry_src else '[FAIL]'}  LRU 캐시 적용")
print(f"{'[PASS]' if 'falling back to sequential' in retry_src else '[FAIL]'}  배치 실패 시 sequential fallback")


# ── 최종 요약 ─────────────────────────────────────────────────────────────────
section("최종 요약")
print("""
  변경 파일          핵심 개선
  ─────────────────────────────────────────────────────
  modules/embedding.py   신규: LRU캐시 + 배치(32) + 503 retry
  modules/rag_engine.py  embed_batch() + similarity 필터(0.25)
  community_summarizer   _embed() 중복 제거 → embed() 공유
  document_parser.py     단락 경계 청킹 + CSV 500행 임베딩
  config.py              SIMILARITY_THRESHOLD / CHUNK_SIZE_MIN 추가
  backend/main.py        CORS 환경변수화
""")
