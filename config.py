import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── API ───────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME = "claude-sonnet-4-6"
MAX_TOKENS = 4096

# ── Document Processing ───────────────────────────────────────────────────────
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".txt", ".md"]

# ── Vector Store (RAG) ────────────────────────────────────────────────────────
VECTOR_DB_PATH = "./data/vector_store"
UPLOAD_PATH = "./data/uploads"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"  # 한국어 지원
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
for _path in [VECTOR_DB_PATH, UPLOAD_PATH, "./data"]:
    Path(_path).mkdir(parents=True, exist_ok=True)
