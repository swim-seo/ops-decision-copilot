# OPS Decision Copilot

> **Domain-adaptive AI operations copilot platform**
> Combines documents, data, and knowledge graphs to support operational decision-making.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ops-decision-copilot.streamlit.app)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Claude API](https://img.shields.io/badge/LLM-Claude%20Sonnet-orange.svg)](https://anthropic.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Overview

OPS Decision Copilot is an AI copilot platform that adapts to **any business domain**.
Upload documents, CSVs, or meeting notes and get:

- **Knowledge Graph** auto-construction (Claude + NetworkX + pyvis)
- **RAG-based document Q&A** (ChromaDB + sentence-transformers)
- **CSV data auto-analysis** (pandas + plotly) with structured answers
- **Decision support**: data recommendations -> check questions -> next actions
- **Daily briefing** with 4 auto-generated cards
- **Streaming responses** for real-time chat experience

7 built-in domain presets (beauty, supply chain, energy, manufacturing, logistics, finance, generic).
Type any domain name and Claude instantly adapts.

---

## Architecture

```
+-------------------------------------------------------------+
|                    app.py  (UI Orchestration)                 |
|  Step 1: Domain Setup -> Step 2: File Upload -> Step 3: Results |
+---------+---------------------+--------------------+----------+
          |                     |                    |
 +--------v--------+  +---------v--------+  +-------v--------+
 | Document        |  | Analytics        |  | Chat Engine    |
 | Pipeline        |  | Engine           |  |                |
 |                 |  |                  |  | chat_copilot   |
 | RAGEngine       |  | data_analyst     |  | route:         |
 | (ChromaDB)      |  | data_chat_engine |  |  data /        |
 |                 |  | query_planner    |  |  doc /         |
 | KnowledgeGraph  |  |                  |  |  combined      |
 | (NetworkX)      |  | 5 question types |  |                |
 |                 |  | CHART / RANKING  |  | DataAnswer ->  |
 | document_parser |  | COMPARISON /     |  | ChatResult     |
 +-----------------+  | RISK / DESCRIBE  |  +----------------+
                      +------------------+
                              |
         +--------------------+--------------------+
         |                    |                    |
+--------v------+  +----------v----+  +-----------v---+
| Claude API    |  | domains/      |  | prompts/      |
| (Anthropic)   |  | presets       |  | templates     |
|               |  |               |  |               |
| claude_client |  | beauty        |  | system_base   |
| domain_adapter|  | supply_chain  |  | summarize     |
+---------------+  | energy / ...  |  | rag_query     |
                   +---------------+  +---------------+
```

### Core Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Domain-agnostic** | `domains/` presets + Claude dynamic domain analysis |
| **Module independence** | `data_analyst.py` has no Streamlit dependency, testable standalone |
| **3-layer routing** | Question -> data / doc / combined auto-classification |
| **Evidence-based answers** | All answers show CSV/document/KG node count badges |
| **Decision support** | Every data query suggests "today/this week/this month" actions |
| **Streaming** | Real-time Claude response streaming via `st.write_stream` |
| **Parallel processing** | ThreadPoolExecutor for KG extraction and combined route |

---

## Core Features

### 1. Domain Adaptation
- 7 built-in domains: Beauty, Supply Chain, Energy, Manufacturing, Logistics, Finance, Generic
- Custom input -> Claude auto-generates entity_types, terminology, theme_color
- Per-domain ChromaDB collection isolation

### 2. Knowledge Graph (3 views)
- **Node Graph**: Interactive pyvis with drill-down (Level 1->2->3)
- **ERD Table View**: Card-based table schema with columns, FK keys, and relationships
- **Data Flow View**: MST -> FACT directional flow with JOIN keys displayed

### 3. Data Chat Engine
5 question types auto-classified:

| Type | Trigger | Output |
|------|---------|--------|
| CHART | Product code (FG-XXX) / chart keywords | Plotly line/bar chart |
| RANKING | TOP / best-selling / seasonal | Horizontal bar + ranking |
| COMPARISON | compare / YoY | Year-over-year bar chart |
| RISK | risk / stockout / CRITICAL | Coverage chart + reorder status |
| DESCRIPTION | everything else | RAG + KG combined |

All answers: **1-line summary** + **3 key metrics** + **chart** + **interpretation** + **next actions (today/this week/this month)**

### 4. Query Planner
One business sentence -> automatic dataset recommendations:
- Pass 1: Keyword matching (schema registry)
- Pass 2a: FK chain expansion (related tables at 50% confidence)
- Pass 2b: Claude refines reasons -> **reason + check question + next action**
- Pass 3: RAG document recommendations

### 5. Daily Briefing
4 auto-generated cards:
- Inventory risk items (CRITICAL/WARNING)
- Channel sales TOP3 (recent month)
- Items needing replenishment (no active orders)
- Anomaly detection (recent 2 months vs previous 2 months +/-50%)

Each card: **1-line summary** + **key metrics** + **3 immediate actions** + **"Continue in chat"** button

### 6. Security
- Prompt injection defense (pattern-based sanitization)
- XSS prevention (ensure_ascii=True for JS embedding)
- Path traversal defense (pathlib-based safe_csv_path)
- Demo usage limit (20 API calls per session)

---

## Adding a New Domain

```python
# 1. Create domains/healthcare.py
PRESET = {
    "entity_types": {
        "patient":   "#2196F3",
        "doctor":    "#4CAF50",
        "facility":  "#FF9800",
        "issue":     "#F44336",
        "decision":  "#4CAF50",
        "metric":    "#607D8B",
        "default":   "#9E9E9E",
    },
    "terminology":       ["EMR", "DRG", "prescription", "diagnosis code"],
    "document_patterns": ["medical records", "admin reports"],
    "analysis_focus":    ["patient safety", "care efficiency", "cost optimization"],
    "theme_color":       "#0284c7",
    "app_icon":          "hospital",
}

# 2. Add one line to domains/__init__.py
from domains.healthcare import PRESET as _healthcare
ALL_PRESETS["healthcare"] = _healthcare
```

Or just type the domain name - Claude generates the config instantly.

---

## Getting Started

```bash
git clone https://github.com/swim-seo/ops-decision-copilot.git
cd ops-decision-copilot
pip install -r requirements.txt

# Set API key (either method)
cp .env.example .env                    # Add ANTHROPIC_API_KEY to .env
# or
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

streamlit run app.py
```

---

## Demo Scenarios

### Scenario 1: Supply Chain Inventory Risk Analysis
1. Click "Sample Data" to load demo data
2. Click "Generate Briefing" -> see 4-card inventory risk overview
3. Chat: `FG-002 demand graph` -> monthly trend chart
4. Chat: `Show CRITICAL inventory items and reorder priorities`

### Scenario 2: Meeting Notes -> Data Connection
1. Upload a meeting notes TXT file
2. AI Analysis tab -> "Extract Action Items" -> auto-linked dataset badges
3. Click "View Data Recommendations" -> see reasons, check questions, next actions

### Scenario 3: New Domain Adaptation
1. In Step 1, type a custom domain (e.g., "healthcare")
2. Claude auto-generates domain-specific entity types, terminology, and theme
3. Upload domain documents -> domain-specific knowledge graph built

---

## Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| LLM | Claude Sonnet (Anthropic) | Korean document processing, long context |
| Vector DB | ChromaDB | Lightweight embedding DB, local/cloud compatible |
| Embedding | paraphrase-multilingual-MiniLM-L12-v2 | Korean semantic search optimization |
| UI | Streamlit | Rapid prototyping, interactive components |
| Graph | NetworkX + pyvis | Intuitive KG construction + interactive HTML rendering |
| Data Analysis | pandas + plotly | Lightweight analysis, interactive charts |
| Domain Adaptation | DomainConfig dataclass | Domain switching without config changes |

---

## Project Structure

```
ops-decision-copilot/
+-- app.py                    # UI Orchestration (Streamlit 3-step flow)
+-- config.py                 # Global settings (API key, paths, colors)
|
+-- domains/                  # Domain preset package
|   +-- __init__.py           # ALL_PRESETS, get_preset()
|   +-- beauty.py             # Beauty/e-commerce
|   +-- supply_chain.py       # Supply chain/inventory
|   +-- energy.py / manufacturing.py / logistics.py / finance.py / generic.py
|
+-- modules/                  # Core business logic
|   +-- claude_client.py      # Claude API wrapper (streaming, retry)
|   +-- rag_engine.py         # ChromaDB vector search
|   +-- knowledge_graph.py    # Entity relationship graph + 3 views
|   +-- domain_adapter.py     # Claude dynamic domain analysis
|   +-- document_parser.py    # PDF/DOCX/CSV parser
|   +-- data_analyst.py       # pandas data analysis functions
|   +-- data_chat_engine.py   # 5 question type classification/response
|   +-- query_planner.py      # Business sentence -> dataset recommendation
|   +-- chat_copilot.py       # Router (data/doc/combined) + streaming
|   +-- prompt_loader.py      # Prompt template loader (system_base injection)
|
+-- prompts/                  # Claude prompt templates
|   +-- system_base.txt       # Shared base prompt (role, rules, domain_context)
|   +-- summarize.txt / action_items.txt / root_cause.txt / report_draft.txt
|   +-- rag_query.txt / chat_routing.txt
|
+-- scripts/                  # Data generation scripts
+-- tests/                    # Test files
+-- data/                     # Sample data (supply chain domain demo)
```

---

## Deployment

- **Live demo**: [ops-decision-copilot.streamlit.app](https://ops-decision-copilot.streamlit.app)
  *(Demo: 20 API call limit per session)*

---

## License

MIT
