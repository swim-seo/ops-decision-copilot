# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
pip install -r requirements.txt
streamlit run app.py
```

API key resolution order: `st.secrets` (Streamlit Cloud) -> `.env` file -> environment variable.
Set `ANTHROPIC_API_KEY` in `.env` for local dev.

## Architecture Overview

Single-file Streamlit app (`app.py`) orchestrating a 3-step flow:

**Step 1** Domain Setup -> **Step 2** File Upload -> **Step 3** Results

All UI state lives in `st.session_state` (initialized in `_init_session()`). Modules in `modules/` contain pure business logic with no Streamlit dependency.

---

## Domain System

`domains/` package holds 7 preset dicts (`beauty`, `supply_chain`, `energy`, `manufacturing`, `logistics`, `finance`, `generic`). Each exports `PRESET` with keys: `entity_types`, `terminology`, `document_patterns`, `analysis_focus`, `theme_color`, `app_icon`.

`domains/__init__.py` exposes `ALL_PRESETS` (dict) and `get_preset(name)` (keyword-matched lookup).

`app.py._build_domain_from_name(name)` -> if name matches a preset, returns `DomainConfig` from preset; otherwise calls `DomainAdapter.analyze_domain()` (one Claude call) to generate config dynamically.

`DomainConfig` (in `domain_adapter.py`) drives everything domain-specific:
- `.collection_name` -> per-domain ChromaDB collection (prevents data mixing across domains)
- `.to_context_string()` -> injected as `{domain_context}` into every Claude prompt
- `.get_entity_types_description()` -> used in KG extraction prompt

---

## File Processing Pipeline

```
upload / sample load
  -> _process_file_contents(entries)   # unified handler for both upload and disk files
      -> document_parser.py
          parse_file()           -> PDF/DOCX/TXT/MD -> plain text
          extract_csv_schema()   -> column names, types, FK candidates -> dict
          extract_python_graph_data() -> AST -> {nodes, edges}
      -> RAGEngine.add_document() -> chunk -> ChromaDB (dedup: deletes existing chunks first)
      -> KnowledgeGraph.build_*() -> NetworkX -> pyvis HTML
      -> ThreadPoolExecutor for parallel Claude KG extraction
```

`KnowledgeGraph` has four build paths:
- `build_from_claude_json()` -- general docs (Claude returns JSON with nodes/edges)
- `build_from_schema_json()` -- `SCHEMA_DEFINITION.json` (tables->nodes, FK->edges)
- `build_from_csv_schema()` -- 2-pass: add table node first, then FK edges after all tables loaded
- `build_from_python_ast()` -- Python files (classes/functions/imports)

KG visualization has 3 tabs:
- **Node Graph**: pyvis with drill-down (Level 1->2->3), `render_html()` uses `net.generate_html()` (NOT `save_graph()`) then writes with `encoding="utf-8"`, then `_inject_ui()` injects drill-down JS.
- **ERD Table View**: Card-based table schema display
- **Data Flow View**: MST -> FACT directional flow

---

## Chat System

### Routing (`chat_copilot.py`)

`detect_route(msg)` classifies into `"data"` | `"doc"` | `"combined"` by keyword matching.

`respond()` dispatches:
- `"doc"` -> RAG + KG lookup -> Claude with `rag_query.txt` prompt
- `"data"` / `"combined"` -> **delegates to `data_chat_engine.analyze()`**

`respond_stream()` provides streaming support:
- `"doc"` -> streams Claude response via `claude.stream()`
- `"data"` / `"combined"` -> yields full text at once (pandas analysis required first)

Returns `ChatResult(text, route, charts, datasets, documents, kg_nodes, metrics)`.

### Data Chat Engine (`data_chat_engine.py`)

5 question types auto-detected, each returns a `DataAnswer`:

| Type | Trigger | Output |
|------|---------|--------|
| `CHART` | Product code `FG-XXX` / chart keywords | Plotly line/bar chart |
| `RANKING` | TOP / best-selling / seasonal | Horizontal bar + ranking |
| `COMPARISON` | compare / YoY | Year-over-year bar chart |
| `RISK` | risk / stockout / CRITICAL | Coverage chart + reorder status |
| `DESCRIPTION` | everything else | RAG + KG combined |

All types call `_claude_interpret()` which appends a "next actions" section (today/this week/this month).

### Query Planner (`query_planner.py`)

`plan(text, rag, kg, claude, domain_context)` -> `QueryPlan`:
- Pass 1: keyword match against `_SCHEMA_REGISTRY` (14 table schemas)
- Pass 2a: FK-chain expansion (related tables added at 50% confidence)
- Pass 2b: Claude refines reasons -> returns `{table: {reason, check_question, next_action}}`
- Pass 3: RAG document recommendations

---

## Prompt System

All prompts in `prompts/*.txt`. `prompt_loader.load_prompt("name", key=value)` loads and substitutes placeholders.

`system_base.txt` contains shared role definition, domain_context injection, and formatting rules (tilde, Korean). Other prompts use `{system_base}` placeholder which is auto-injected by `load_prompt()`.

---

## Security

- Prompt injection: `sanitize_input()` in `chat_copilot.py` strips role-override patterns
- XSS: `json.dumps(ensure_ascii=True)` in `knowledge_graph.py` for JS embedding
- Path traversal: `_safe_csv_path()` in `data_analyst.py` restricts to DATA_DIR
- Demo limit: 20 API calls per session (chat + AI analysis tabs)

## API Client (`claude_client.py`)

- `generate()`: single prompt -> text (with exponential backoff retry for 429/529)
- `generate_with_system()`: system + user prompt
- `stream()`: generator yielding text chunks for streaming
- `TOKENS` dict: recommended max_tokens per use case (summary: 1500, chat: 2000, briefing: 2500, kg: 1000)
- API key via `config._get_secret()` (unified, no duplication)

## Performance

- KG extraction: `ThreadPoolExecutor(max_workers=3)` for parallel Claude calls
- Combined route: parallel RAG/KG/CSV data fetching via ThreadPoolExecutor
- ChromaDB: `delete_document()` before `add_document()` prevents duplicate chunks

## Persistent Storage

- `./data/vector_store/` -- ChromaDB (persists between sessions)
- `./data/graph.html` -- overwritten on each `render_html()` call
- `./data/` -- sample CSVs, `SCHEMA_DEFINITION.json`

Directories are auto-created by `config.py` at import time.
