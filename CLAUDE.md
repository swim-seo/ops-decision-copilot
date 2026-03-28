# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (requires ANTHROPIC_API_KEY in .env)
streamlit run app.py
```

API key resolution order: `st.secrets` (Streamlit Cloud) → `.env` file → environment variable.

## Architecture Overview

This is a single-page Streamlit app with a 3-step flow:

**Step 1 → Step 2 → Step 3**
Domain Setup → File Upload → Results (KG + AI Analysis)

### Data Flow

```
User uploads file
  → document_parser.py (parse_file / extract_csv_schema / extract_python_graph_data)
  → RAGEngine.add_document() → ChromaDB vector store
  → KnowledgeGraph.build_*() → NetworkX + pyvis HTML
  → Claude analysis via prompts/*.txt templates
```

### Key Modules

| File | Role |
|------|------|
| `app.py` | All Streamlit UI, session state, page routing |
| `config.py` | Constants + `_get_secret()` for API key resolution |
| `modules/claude_client.py` | Thin Anthropic SDK wrapper (`generate`, `generate_with_system`) |
| `modules/rag_engine.py` | ChromaDB ingestion + cosine-similarity search |
| `modules/knowledge_graph.py` | NetworkX graph builder + pyvis HTML renderer |
| `modules/document_parser.py` | PDF/DOCX/TXT/CSV/Python → text + AST extraction |
| `modules/domain_adapter.py` | `DomainConfig` dataclass + Claude-powered domain analyzer |
| `modules/prompt_loader.py` | Loads `prompts/*.txt` and replaces `{placeholders}` |

### Domain Adaptation

`DomainConfig` drives everything domain-specific:
- `collection_name` property → per-domain ChromaDB collection (prevents data mixing)
- `to_context_string()` → injected into every Claude prompt as `{domain_context}`
- `get_entity_types_description()` → used in KG entity extraction prompt

`app.py` has inline presets (`_PRESETS`) for 7 industries (뷰티/공급망/에너지/제조/물류/금융/기타). If domain name matches a preset, `_build_domain_from_name()` uses it directly without calling Claude. Otherwise `DomainAdapter.analyze_domain()` calls Claude and falls back to default config on failure.

### Knowledge Graph Build Paths

`knowledge_graph.py` has four distinct builders depending on file type:
- `build_from_claude_extraction()` — general documents (Claude extracts entities/relations as JSON)
- `build_from_schema_json()` — `SCHEMA_DEFINITION.json` (tables → nodes, FK relationships → edges)
- `build_from_csv_schema()` — CSV files (2-pass: add nodes first, then FK edges)
- `build_from_python_graph_data()` — Python files (AST: classes/functions/imports)

### Prompt Templates

All prompts live in `prompts/*.txt` with `{placeholder}` syntax. Load via `modules/prompt_loader.load_prompt("name", key=value)`. All templates accept `{domain_context}` which is injected in `app.py` before calling Claude.

### Step 3 Layout

Step 3 uses a `3:2` two-column layout:
- **Left (`col_main`)**: Knowledge graph (pyvis HTML, height=620) + AI analysis tabs (요약/액션아이템/원인분석/보고서) + RAG search + node lookup
- **Right (`col_chat`)**: Data chat panel + daily briefing button

### Chat Panel (`col_chat`)

Handles three intents detected by `_detect_chat_intent()`:

| Intent | Trigger keywords | Handler |
|--------|-----------------|---------|
| `graph` | 그래프, 차트, 그려줘, 보여줘 | `_handle_chat_graph()` → Plotly line chart |
| `analysis` | 판매, 재고, 발주, 여름, 계절, 잘팔리 | `_handle_chat_analysis()` → CSV summary → Claude |
| `rag` | everything else | `_handle_chat_rag()` → KG + RAG combined |

`_handle_chat_graph()` extracts `FG-XXX` / `PRDXXX` codes via regex, joins `MST_PART.csv` to resolve product names, then plots `FACT_MONTHLY_SALES.csv`. Falls back to channel-total chart if no code found.

`_generate_daily_briefing()` loads three CSVs (`FACT_INVENTORY`, `FACT_MONTHLY_SALES`, `FACT_REPLENISHMENT_ORDER`), builds a pandas summary, then calls Claude once. Returns `(text, [fig1, fig2])`.

### Demo Usage Limit

`chat_api_calls` session state counter increments on every chat response and daily briefing call. Limit is `_DEMO_LIMIT = 20` (defined inside the `elif step == 3:` block). When exhausted: input/buttons disabled, red error banner shown. Badge color: green (>5 left) → amber (1–5) → red (0).

Five preset question buttons (`_PRESETS_Q`) set `chat_preset_input` in session state, which is consumed as `user_input` on the next rerun (avoids `st.chat_input` value injection issues).

### Session State Keys

`st.session_state` keys managed in `_init_session()`:
- `documents` — dict of filename → parsed text
- `rag` — `RAGEngine` instance (recreated when domain/collection changes)
- `claude` — `ClaudeClient` instance
- `kg` — `KnowledgeGraph` instance
- `domain_config` — serialized `DomainConfig` dict (or `None`)
- `step` — current UI step (1/2/3)
- `chat_history` — list of `{"role", "content", "charts"}` dicts
- `chat_api_calls` — int, increments each time Claude is called from chat
- `chat_preset_input` — `str | None`, set by preset buttons, consumed once on rerun

### Persistent Storage

- Vector store: `./data/vector_store/` (ChromaDB, persists between sessions)
- Graph HTML: `./data/graph.html` (overwritten each render)
- Demo CSVs: `./data/` — `FACT_MONTHLY_SALES`, `FACT_INVENTORY`, `FACT_REPLENISHMENT_ORDER`, `MST_PART`, `MST_CHANNEL`, etc.

These directories are auto-created by `config.py` at import time.
