# RAG Engine Performance Analysis & Improvement Recommendations

**Date**: 2026-05-08  
**Scope**: `modules/rag_engine.py`, `modules/document_parser.py`, `modules/community_summarizer.py`, `modules/chat_copilot.py`

---

## Current Architecture Summary

| Component | Current Implementation | Notes |
|-----------|----------------------|-------|
| Embedding model | `paraphrase-multilingual-MiniLM-L12-v2` (384-dim) | HF Inference API, HTTP per chunk |
| Vector store | Supabase pgvector, cosine similarity | RPC `match_document_chunks` |
| Chunking | Fixed-size 800 chars, 150 overlap, boundary-aware | `chunk_text()` in document_parser.py |
| Retrieval | TOP_K=5 pure vector similarity | No reranking, no hybrid |
| GraphRAG | Community summaries + 2-hop KG traversal | Layered on top of RAG |
| Reranking | None | Raw similarity scores used directly |
| Caching | None | Every query hits HF API + Supabase |

---

## Identified Bottlenecks (Priority Order)

### 1. CRITICAL: Sequential Embedding — N chunks = N HTTP calls
- `add_document()` embeds each chunk individually in a for-loop
- A 10-page PDF → ~30 chunks → 30 separate HTTP requests to HuggingFace API
- Each request: ~200–500ms → total upload: 6–15 seconds per document
- **Same issue in `community_summarizer.py`**: one HF call per community summary

### 2. HIGH: No Query Embedding Cache
- `query()` calls `_embed(question)` on every single chat request
- Same question asked twice → 2 identical HF API calls
- `retrieve_community_context()` also embeds separately from the main query

### 3. HIGH: Duplicate Embedding Work (doc route)
- In `respond_stream()` / `_handle_doc()`: `_build_graphrag_context()` calls `_embed(question)` in `retrieve_community_context()`
- Then `rag.query(msg)` calls `_embed(question)` again independently
- Same question embedded **twice** per doc-route request

### 4. MEDIUM: Fixed Character-Count Chunking
- Current: 800 chars with 150 overlap (character-count based)
- Problem: cuts mid-sentence on Korean text, splits logical units (tables, bullet lists)
- No semantic awareness — a paragraph about "decision A" may span two chunks

### 5. MEDIUM: No Reranking
- Cosine similarity in 384-dim space is imprecise for nuanced business questions
- False positives (similar embeddings but irrelevant content) degrade answer quality
- TOP_K=5 with no diversity → may return 5 similar chunks from one section

### 6. LOW: No Hybrid Search (BM25 + Vector)
- Exact keyword matches (e.g., product codes "FG-001", person names) are missed by pure vector search
- Korean business documents often contain exact terms critical to the query

---

## Improvement Recommendations

### Quick Wins (Low effort, high impact)

#### A. Batch Embedding (Fixes bottleneck #1)
HuggingFace Inference API supports batch input:
```python
# Current (N calls)
for chunk in chunks:
    embedding = _embed(chunk)  # 1 HTTP call each

# Improved (1 call for all chunks)
def _embed_batch(texts: list[str]) -> list[list[float]]:
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    resp = requests.post(_HF_URL, headers=headers, json={"inputs": texts}, timeout=60)
    resp.raise_for_status()
    return resp.json()  # Returns list of embeddings
```
Expected improvement: **10–30x faster document upload**

#### B. Query Embedding Cache (Fixes bottleneck #2 & #3)
```python
from functools import lru_cache

@lru_cache(maxsize=256)
def _embed_cached(text: str) -> tuple[float, ...]:
    result = _embed(text)
    return tuple(result)  # hashable for LRU cache
```
Or pass the pre-computed embedding between `retrieve_community_context()` and `rag.query()`:
```python
# In _handle_doc() — embed once, use twice
q_embedding = _embed(msg)
community_ctx = retrieve_community_context_with_embedding(q_embedding, collection_name)
hits = rag.query_with_embedding(q_embedding, n_results=4)
```
Expected improvement: **~50% latency reduction** on doc-route queries

#### C. Increase TOP_K with Score Threshold
```python
# In config.py
TOP_K_RESULTS = 5       # current
TOP_K_FETCH = 10        # fetch more, filter by threshold
SIMILARITY_THRESHOLD = 0.65  # discard low-quality hits
```
```python
# In rag_engine.py query()
rows = _sb.rpc(_RPC, {"query_embedding": ..., "match_count": TOP_K_FETCH})
hits = [r for r in rows if r["similarity"] >= SIMILARITY_THRESHOLD][:TOP_K_RESULTS]
```

---

### Medium-Term Improvements

#### D. Cross-Encoder Reranking via HuggingFace
After initial vector retrieval (TOP_K=10), rerank with a cross-encoder:
```python
# Use cross-encoder/ms-marco-MiniLM-L-6-v2 or 
# cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 (multilingual)
_RERANK_URL = "https://api-inference.huggingface.co/models/cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

def _rerank(question: str, chunks: list[str]) -> list[float]:
    pairs = [{"text": question, "text_pair": chunk} for chunk in chunks]
    resp = requests.post(_RERANK_URL, headers=headers, json={"inputs": pairs})
    return resp.json()  # List of scores
```
Pattern: retrieve TOP_K=10 by vector → rerank → return top 3–5
Expected improvement: **Significant precision boost** for complex queries

#### E. Semantic Chunking (Token-boundary aware)
Replace character counting with sentence/paragraph-aware splitting:
```python
def chunk_text_semantic(text: str, max_tokens: int = 512) -> list[str]:
    """Split by paragraphs first, then merge small ones, split large ones."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = []
    current_len = 0
    
    for para in paragraphs:
        para_len = len(para)
        if current_len + para_len > max_tokens * 2 and current:  # ~chars
            chunks.append("\n\n".join(current))
            current = [para]
            current_len = para_len
        else:
            current.append(para)
            current_len += para_len
    
    if current:
        chunks.append("\n\n".join(current))
    return chunks
```

#### F. Hybrid Search (BM25 + Vector)
Supabase supports full-text search alongside pgvector. Add BM25-weighted retrieval:

**Supabase SQL addition:**
```sql
-- Add tsvector column for full-text search
ALTER TABLE document_chunks ADD COLUMN ts_content tsvector
    GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED;
CREATE INDEX idx_chunks_fts ON document_chunks USING gin(ts_content);
```

**Python hybrid query:**
```python
def query_hybrid(self, question: str, n_results: int = TOP_K_RESULTS):
    """Combine vector similarity + BM25 keyword match."""
    # 1. Vector search (existing)
    vector_hits = self.query(question, n_results=n_results * 2)
    
    # 2. BM25 keyword search via Supabase REST
    # Uses websearch_to_tsquery for Korean-friendly parsing
    keyword_hits = self._keyword_search(question, n_results=n_results * 2)
    
    # 3. Reciprocal Rank Fusion (RRF)
    return _rrf_merge(vector_hits, keyword_hits, top_k=n_results)
```

---

### Model Upgrade Options

#### G. Better Korean Embedding Model
| Model | Dims | Notes |
|-------|------|-------|
| Current: `paraphrase-multilingual-MiniLM-L12-v2` | 384 | Fast, decent Korean |
| `jhgan/ko-sroberta-multitask` | 768 | Korean-specialized, better semantic |
| `snunlp/KR-ELECTRA-discriminator` | 768 | Korean ELECTRA, stronger |
| `intfloat/multilingual-e5-large` | 1024 | Best multilingual, slower |

**Recommendation**: `jhgan/ko-sroberta-multitask` for best Korean business document understanding with reasonable inference cost. Requires re-embedding all stored documents.

**Migration path**: Add `embedding_model_version` column to `document_chunks`, support gradual migration per collection.

---

## Implementation Priority Matrix

| Improvement | Effort | Impact | Recommended Order |
|-------------|--------|--------|-------------------|
| A. Batch embedding | Low | Very High (10–30x upload speed) | **1st** |
| B. Query embedding cache + dedup | Low | High (50% query latency) | **2nd** |
| C. Score threshold filter | Very Low | Medium | **3rd** |
| D. Cross-encoder reranking | Medium | High (precision) | **4th** |
| E. Semantic chunking | Medium | Medium | **5th** |
| F. Hybrid BM25+vector | High | High (recall for keywords) | **6th** |
| G. Model upgrade | High | High (quality) | **7th** |

---

## Files to Modify

| File | Change |
|------|--------|
| `modules/rag_engine.py` | Batch embedding, query cache, score threshold |
| `modules/document_parser.py` | Semantic chunking option |
| `modules/community_summarizer.py` | Batch embedding, share query embedding |
| `modules/chat_copilot.py` | Single embedding per request passed to both RAG and GraphRAG |
| `config.py` | `TOP_K_FETCH`, `SIMILARITY_THRESHOLD`, `EMBEDDING_MODEL` |
| `scripts/vector_migration.sql` | BM25 tsvector column (optional) |
