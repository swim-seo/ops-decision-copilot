"""
[역할] 전역 설정 파일
앱 전체에서 공통으로 사용하는 상수와 환경 변수를 한 곳에 정의합니다.
  - API 키·모델명 등 Claude 연결 설정
  - 문서 청킹 크기, 지원 파일 형식
  - RAG 임베딩 모델·컬렉션 설정 (벡터 저장소: Supabase pgvector)
  - Streamlit UI 기본 타이틀·아이콘
  - 지식 그래프 출력 경로, 엔티티 색상 매핑
  - data/ 등 필요 디렉터리 자동 생성
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)  # 로컬 개발: .env 파일 읽기 (환경변수 덮어쓰기)


def _get_secret(key: str) -> str:
    """
    API 키 조회 우선순위:
      1) st.secrets  — Streamlit Cloud 배포 환경
      2) .env 파일   — 로컬 개발 환경
      3) 환경변수    — CI/CD 등 기타 환경
    """
    # 1) Streamlit secrets (Cloud 배포 시)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            val = st.secrets[key]
            if val:
                return str(val)
    except Exception:
        pass
    # 2) .env / 환경변수
    return os.getenv(key, "")


# ── API ───────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = _get_secret("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-sonnet-4-6"
MAX_TOKENS = 4096

# ── Supabase (선택사항 — 없으면 CSV fallback) ─────────────────────────────────
SUPABASE_URL = _get_secret("SUPABASE_URL")
SUPABASE_KEY = _get_secret("SUPABASE_KEY")

# ── Document Processing ───────────────────────────────────────────────────────
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".txt", ".md"]

# ── RAG (Supabase pgvector) ───────────────────────────────────────────────────
UPLOAD_PATH = "./data/uploads"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"  # 한국어 지원, 384차원
DEFAULT_COLLECTION_NAME = "domain_docs"
TOP_K_RESULTS = 5

# ── App UI (도메인 설정 전 기본값) ────────────────────────────────────────────
APP_TITLE = "AI 운영 코파일럿"
APP_ICON = "🤖"

# ── Knowledge Graph ───────────────────────────────────────────────────────────
GRAPH_OUTPUT_PATH = "./data/graph.html"

# 기본 엔티티 색상 (도메인 설정 전 fallback)
DEFAULT_ENTITY_COLORS = {
    # 일반 엔티티
    "person":       "#2196F3",
    "organization": "#9C27B0",
    "process":      "#FF9800",
    "resource":     "#00BCD4",
    "issue":        "#F44336",
    "decision":     "#4CAF50",
    "metric":       "#607D8B",
    # 스키마 테이블 유형
    "master_table": "#1565C0",  # 진한 파랑 — 마스터 테이블
    "fact_table":   "#E65100",  # 진한 주황 — 팩트 테이블
    # CSV/Python 추출 유형
    "csv_table":    "#00796B",  # 초록 — CSV 테이블
    "file":         "#5C6BC0",  # 인디고 — Python 파일
    "class":        "#7B1FA2",  # 보라 — 클래스
    "function":     "#0288D1",  # 하늘 — 함수
    "method":       "#0097A7",  # 청록 — 메서드
    "module":       "#558B2F",  # 올리브 — 모듈
    "default":      "#9E9E9E",
}

# ── Directories ───────────────────────────────────────────────────────────────
for _path in [UPLOAD_PATH, "./data"]:
    Path(_path).mkdir(parents=True, exist_ok=True)
