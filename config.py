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
COLLECTION_NAME = "beauty_docs"
TOP_K_RESULTS = 5

# ── App UI ────────────────────────────────────────────────────────────────────
APP_TITLE = "뷰티 AI 운영 코파일럿"
APP_ICON = "💄"
COMPANY_NAME = "Beauty Co."

# ── Knowledge Graph ───────────────────────────────────────────────────────────
GRAPH_OUTPUT_PATH = "./data/graph.html"

ENTITY_COLORS = {
    "person":     "#E91E8C",  # 핑크
    "product":    "#FF5722",  # 오렌지레드
    "brand":      "#9C27B0",  # 퍼플
    "department": "#3F51B5",  # 인디고
    "campaign":   "#FF9800",  # 앰버
    "issue":      "#F44336",  # 레드
    "decision":   "#4CAF50",  # 그린
    "ingredient": "#00BCD4",  # 시안
    "metric":     "#607D8B",  # 블루그레이
    "default":    "#9E9E9E",  # 그레이
}

# ── Directories ───────────────────────────────────────────────────────────────
for _path in [VECTOR_DB_PATH, UPLOAD_PATH, "./data"]:
    Path(_path).mkdir(parents=True, exist_ok=True)
