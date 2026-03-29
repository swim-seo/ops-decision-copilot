# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
pip install -r requirements.txt
streamlit run app.py
```

API key resolution order: `st.secrets` (Streamlit Cloud) → `.env` file → environment variable.
Set `ANTHROPIC_API_KEY` in `.env` for local dev.

## Architecture Overview

Single-file Streamlit app (`app.py`) orchestrating a 3-step flow:

**Step 1** Domain Setup → **Step 2** File Upload → **Step 3** Results

All UI state lives in `st.session_state` (initialized in `_init_session()`). Modules in `modules/` contain pure business logic with no Streamlit dependency.

---

## Domain System

`domains/` package holds 7 preset dicts (`beauty`, `supply_chain`, `energy`, `manufacturing`, `logistics`, `finance`, `generic`). Each exports `PRESET` with keys: `entity_types`, `terminology`, `document_patterns`, `analysis_focus`, `theme_color`, `app_icon`.

`domains/__init__.py` exposes `ALL_PRESETS` (dict) and `get_preset(name)` (keyword-matched lookup).

`app.py._build_domain_from_name(name)` → if name matches a preset, returns `DomainConfig` from preset; otherwise calls `DomainAdapter.analyze_domain()` (one Claude call) to generate config dynamically.

`DomainConfig` (in `domain_adapter.py`) drives everything domain-specific:
- `.collection_name` → per-domain ChromaDB collection (prevents data mixing across domains)
- `.to_context_string()` → injected as `{domain_context}` into every Claude prompt
- `.get_entity_types_description()` → used in KG extraction prompt

---

## File Processing Pipeline

```
upload / sample load
  → document_parser.py
      parse_file()           → PDF/DOCX/TXT/MD → plain text
      extract_csv_schema()   → column names, types, FK candidates → dict
      extract_python_graph_data() → AST → {nodes, edges}
  → RAGEngine.add_document() → chunk → ChromaDB
  → KnowledgeGraph.build_*() → NetworkX → pyvis HTML
```

`KnowledgeGraph` has four build paths:
- `build_from_claude_extraction()` — general docs (Claude returns JSON with nodes/edges)
- `build_from_schema_json()` — `SCHEMA_DEFINITION.json` (tables→nodes, FK→edges)
- `build_from_csv_schema()` — 2-pass: add table node first, then FK edges after all tables loaded
- `build_from_python_ast()` — Python files (classes/functions/imports)

`render_html()` uses `net.generate_html()` (NOT `save_graph()` — that omits encoding on Windows) then writes with `encoding="utf-8"`, then `_inject_ui()` injects drill-down JS (Level 1→2→3).

---

## Chat System

### Routing (`chat_copilot.py`)

`detect_route(msg)` classifies into `"data"` | `"doc"` | `"combined"` by keyword matching.

`respond()` dispatches:
- `"doc"` → `_handle_doc()` — RAG + KG lookup → Claude with `rag_query.txt` prompt
- `"data"` / `"combined"` → **delegates to `data_chat_engine.analyze()`**

Returns `ChatResult(text, route, charts, datasets, documents, kg_nodes, metrics)`.

### Data Chat Engine (`data_chat_engine.py`)

5 question types auto-detected, each returns a `DataAnswer`:

| Type | Trigger | Output |
|------|---------|--------|
| `CHART` | Product code `FG-XXX` / chart keywords | Plotly line/bar chart |
| `RANKING` | TOP / 잘팔리 / 계절 | Horizontal bar + ranking |
| `COMPARISON` | 비교 / YoY / 전년 | Year-over-year bar chart |
| `RISK` | 위험 / 품절 / CRITICAL | Coverage chart + reorder status |
| `DESCRIPTION` | everything else | RAG + KG combined |

All types call `_claude_interpret()` which appends a `## 다음 할 일` section (오늘/이번 주/이번 달) to every answer.

### Query Planner (`query_planner.py`)

`plan(text, rag, kg, claude, domain_context)` → `QueryPlan`:
- Pass 1: keyword match against `_SCHEMA_REGISTRY` (13 table schemas)
- Pass 2a: FK-chain expansion (related tables added at 50% confidence)
- Pass 2b: Claude refines reasons → returns `{table: {reason, check_question, next_action}}`
- Pass 3: RAG document recommendations

`DatasetRecommendation` fields: `table_name`, `confidence`, `reason`, `check_question`, `next_action`, `is_expanded`.

---

## Session State Keys

Managed in `_init_session()`:

| Key | Type | Purpose |
|-----|------|---------|
| `documents` | `dict[str, str]` | filename → parsed text |
| `rag` | `RAGEngine` | recreated on domain change |
| `claude` | `ClaudeClient` | Anthropic SDK wrapper |
| `kg` | `KnowledgeGraph` | NetworkX graph |
| `domain_config` | `dict \| None` | serialized DomainConfig |
| `step` | `int` | current UI step (1/2/3) |
| `chat_history` | `list` | `{role, content, charts, datasets, documents, kg_nodes, route, metrics}` |
| `chat_api_calls` | `int` | increments each LLM call; demo limit = 20 |
| `chat_preset_input` | `str \| None` | set by chat preset buttons, consumed once |
| `pending_chat_message` | `str \| None` | set by briefing/planner buttons for auto-send |
| `qp_input` | `str` | last query planner input text |
| `qp_result` | `QueryPlan \| None` | last query planner result |
| `briefing_cards` | `list \| None` | 4-card daily briefing data |

`pending_chat_message` and `chat_preset_input` are both consumed via `st.session_state.pop()` before `st.chat_input`, used as `user_input` fallback for auto-send behavior.

---

## Step 3 Layout

```
expander: 업무 문장 → 데이터 추천  (query planner)
expander: 일일 브리핑  (2×2 grid of 4 cards)
divider
col_main (3/5) | col_chat (2/5)
  KG (pyvis HTML)   |  chat header + preset buttons
  reextract expander|  chat history container (height=460)
  divider           |  exhausted banner
  tabs: AI분석 / 문서검색(RAG) / 번호조회
    sub-tabs: 요약 / 액션아이템 / 원인분석 / 보고서
```

---

## Prompt Templates

All in `prompts/*.txt` with `{placeholder}` syntax. Load with `prompt_loader.load_prompt("name", key=value)`. All accept `{domain_context}` injected from `DomainConfig.to_context_string()`.

---

## Persistent Storage

- `./data/vector_store/` — ChromaDB (persists between sessions)
- `./data/graph.html` — overwritten on each `render_html()` call
- `./data/` — sample CSVs (`FACT_MONTHLY_SALES`, `FACT_INVENTORY`, `FACT_REPLENISHMENT_ORDER`, `MST_PRODUCT`, `MST_CHANNEL`, `SCHEMA_DEFINITION.json`)

Directories are auto-created by `config.py` at import time.
