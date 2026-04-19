import os
from pathlib import Path
from dotenv import load_dotenv

_ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=True)


def _get_secret(key: str) -> str:
    return os.getenv(key, "")


# ── API ───────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = _get_secret("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-sonnet-4-6"
MAX_TOKENS = 4096

# ── Supabase ──────────────────────────────────────────────────────────────────
SUPABASE_URL = _get_secret("SUPABASE_URL")
SUPABASE_KEY = _get_secret("SUPABASE_KEY")

# ── Document Processing ───────────────────────────────────────────────────────
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".txt", ".md"]

# ── RAG ───────────────────────────────────────────────────────────────────────
UPLOAD_PATH = "./data/uploads"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_COLLECTION_NAME = "domain_docs"
TOP_K_RESULTS = 5

# ── Knowledge Graph ───────────────────────────────────────────────────────────
GRAPH_OUTPUT_PATH = "./data/graph.html"

DEFAULT_ENTITY_COLORS = {
    "person":       "#2196F3",
    "organization": "#9C27B0",
    "process":      "#FF9800",
    "resource":     "#00BCD4",
    "issue":        "#F44336",
    "decision":     "#4CAF50",
    "metric":       "#607D8B",
    "master_table": "#1565C0",
    "fact_table":   "#E65100",
    "csv_table":    "#00796B",
    "file":         "#5C6BC0",
    "class":        "#7B1FA2",
    "function":     "#0288D1",
    "method":       "#0097A7",
    "module":       "#558B2F",
    "default":      "#9E9E9E",
}

# ── Directories ───────────────────────────────────────────────────────────────
for _path in [UPLOAD_PATH, "./data"]:
    Path(_path).mkdir(parents=True, exist_ok=True)
