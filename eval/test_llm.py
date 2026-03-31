#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 답변 품질 평가 — LLM-as-judge (Claude 자동 채점)

실제 앱 동작과 동일한 조건으로 측정:
  1. 도메인별 Supabase 테이블에서 LIMIT 50 데이터 로드
  2. RAG 엔진으로 상위 3개 청크 검색 (문서 있을 때)
  3. KnowledgeGraph에서 관련 엔티티 관계 조회
  4. 위 컨텍스트를 결합하여 Claude API 답변 생성
  5. required_keywords 충족 여부 + LLM-as-judge 채점

테스트셋 형식 (eval/llm_testset.json):
  {
    "question": "재고 위험 상품 알려줘",
    "reference_answer": "CRITICAL 등급 상품 목록과 커버리지 수치",
    "required_keywords": ["CRITICAL", "커버리지", "발주"],
    "domain": "beauty_ecommerce"
  }

채점 기준:
  - 5점: reference_answer 핵심 포함 + required_keywords 2개 이상
  - 4점: reference_answer 핵심 포함 (키워드 1개 이상)
  - 3점: 관련 있지만 키워드 미충족
  - 2점: 부분적으로만 관련
  - 1점: 무관하거나 오답

실행: python eval/test_llm.py
"""
import sys
import json
import os
import requests
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from modules.claude_client import ClaudeClient
from modules.rag_engine import RAGEngine
from modules.knowledge_graph import KnowledgeGraph
from modules.document_parser import extract_csv_schema
from config import DEFAULT_COLLECTION_NAME

TESTSET_PATH = Path(__file__).parent / "llm_testset.json"

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
_SB_HEADERS  = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

# 도메인 레이블 → Supabase 테이블 목록
DOMAIN_TABLES = {
    "beauty_ecommerce": [
        "beauty_mst_product", "beauty_mst_supplier", "beauty_mst_channel",
        "beauty_fact_monthly_sales", "beauty_fact_inventory",
        "beauty_fact_replenishment_order", "beauty_fact_stockout_event",
    ],
    "supply_chain": [
        "supply_mst_part", "supply_mst_supplier", "supply_mst_warehouse",
        "supply_fact_inventory", "supply_fact_order",
    ],
    "energy": [
        "energy_mst_plant", "energy_mst_meter", "energy_mst_region",
        "energy_fact_daily_usage", "energy_fact_monthly_bill", "energy_fact_outage",
    ],
    "manufacturing": [
        "manufacturing_mst_product", "manufacturing_mst_equipment", "manufacturing_mst_line",
        "manufacturing_fact_production", "manufacturing_fact_defect", "manufacturing_fact_maintenance",
    ],
    "logistics": [
        "logistics_mst_hub", "logistics_mst_vehicle", "logistics_mst_route",
        "logistics_fact_delivery", "logistics_fact_delay", "logistics_fact_cost",
    ],
    "finance": [
        "finance_mst_product", "finance_mst_customer", "finance_mst_branch",
        "finance_fact_transaction", "finance_fact_risk", "finance_fact_performance",
    ],
}


# ── 1. Supabase 데이터 로드 ────────────────────────────────────────────────────
def _fetch_supabase(table: str, limit: int = 50) -> list[dict]:
    """Supabase REST API로 테이블 데이터를 조회합니다."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=_SB_HEADERS,
            params={"select": "*", "limit": limit},
            timeout=10,
        )
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def _build_supabase_context(domain: str) -> str:
    """도메인 테이블에서 데이터를 조회해 컨텍스트 문자열로 변환합니다."""
    tables = DOMAIN_TABLES.get(domain, [])
    parts = []
    for table in tables:
        rows = _fetch_supabase(table, limit=50)
        if not rows:
            continue
        cols = list(rows[0].keys())
        header = f"[테이블: {table}] 컬럼: {cols}"
        sample = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows[:10])
        parts.append(f"{header}\n샘플 데이터(10행):\n{sample}")
    return "\n\n".join(parts) if parts else "(Supabase 데이터 없음)"


# ── 2. RAG 컨텍스트 ────────────────────────────────────────────────────────────
def _build_rag_context(rag: RAGEngine, question: str) -> str:
    """RAG 엔진으로 질문과 유사한 상위 3개 청크를 반환합니다."""
    if rag.document_count() == 0:
        return ""
    hits = rag.query(question, n_results=3)
    if not hits:
        return ""
    parts = [f"[문서 출처: {h['filename']}]\n{h['text']}" for h in hits]
    return "\n\n---\n\n".join(parts)


# ── 3. KG 컨텍스트 ────────────────────────────────────────────────────────────
def _build_kg_context(kg: KnowledgeGraph, question: str) -> str:
    """질문 키워드로 지식그래프에서 관련 엔티티·관계를 검색합니다."""
    if not kg.graph or len(kg.graph.nodes) == 0:
        return ""
    # 질문에서 의미 있는 단어(3자 이상) 추출해서 KG 검색
    keywords = [w for w in question.split() if len(w) >= 3]
    all_nodes = []
    all_edges = []
    seen = set()
    for kw in keywords[:3]:
        result = kg.query_by_id(kw)
        for node in result.get("matched_nodes", []) + result.get("connected_nodes", []):
            nid = node.get("id", "")
            if nid and nid not in seen:
                seen.add(nid)
                all_nodes.append(f"  - {nid} ({node.get('type', '')}): {node.get('title', '')[:80]}")
        for edge in result.get("edges", []):
            e_str = f"  {edge['from']} --[{edge.get('relation','')}]--> {edge['to']}"
            if e_str not in all_edges:
                all_edges.append(e_str)
    if not all_nodes:
        return ""
    lines = ["[지식그래프 관련 엔티티]"] + all_nodes
    if all_edges:
        lines += ["[관계]"] + all_edges[:10]
    return "\n".join(lines)


# ── 4. 답변 생성 ──────────────────────────────────────────────────────────────
def generate_answer(
    claude: ClaudeClient,
    rag: RAGEngine,
    kg: KnowledgeGraph,
    question: str,
    domain: str,
) -> str:
    """실제 앱과 동일하게: Supabase 데이터 + RAG + KG 컨텍스트로 답변 생성."""
    sb_ctx  = _build_supabase_context(domain)
    rag_ctx = _build_rag_context(rag, question)
    kg_ctx  = _build_kg_context(kg, question)

    context_parts = []
    if sb_ctx:
        context_parts.append(f"## Supabase 실제 데이터\n{sb_ctx}")
    if rag_ctx:
        context_parts.append(f"## 관련 문서 (RAG)\n{rag_ctx}")
    if kg_ctx:
        context_parts.append(f"## 지식그래프 관계\n{kg_ctx}")

    full_context = "\n\n".join(context_parts) if context_parts else "(컨텍스트 없음)"

    prompt = (
        f"당신은 {domain} 도메인 전문 AI 운영 코파일럿입니다.\n"
        f"아래 실제 데이터와 관련 정보를 기반으로 질문에 구체적이고 정확하게 답하세요.\n\n"
        f"{full_context}\n\n"
        f"## 질문\n{question}"
    )
    try:
        return claude.generate(prompt, max_tokens=800)
    except Exception as e:
        return f"답변 생성 실패: {e}"


# ── 5. 채점 ───────────────────────────────────────────────────────────────────
JUDGE_PROMPT = """당신은 AI 답변 품질 평가 전문가입니다.

[질문]
{question}

[기준 답변 (reference_answer)]
{reference_answer}

[필수 키워드]
{required_keywords}

[평가 대상 답변]
{actual_answer}

아래 기준으로 1~5점 채점하세요.
- 5점: reference_answer 핵심 포함 + 필수 키워드 2개 이상 존재
- 4점: reference_answer 핵심 포함 (키워드 1개 이상)
- 3점: 관련 있지만 필수 키워드 미충족
- 2점: 부분적으로만 관련
- 1점: 무관하거나 오답

점수와 한 줄 이유만 JSON으로 반환 (다른 텍스트 없이):
{{"score": <1-5>, "reason": "<한 줄 이유>"}}"""


def _count_keywords(answer: str, keywords: list[str]) -> int:
    """답변에 포함된 required_keywords 개수를 반환합니다."""
    answer_lower = answer.lower()
    return sum(1 for kw in keywords if kw.lower() in answer_lower)


def judge_answer(
    claude: ClaudeClient,
    question: str,
    reference: str,
    required_keywords: list[str],
    actual: str,
) -> dict:
    """LLM-as-judge 채점: Claude로 1~5점 평가."""
    kw_hit = _count_keywords(actual, required_keywords)

    prompt = JUDGE_PROMPT.format(
        question=question,
        reference_answer=reference,
        required_keywords=", ".join(required_keywords),
        actual_answer=actual,
    )
    try:
        raw = claude.generate(prompt, max_tokens=200)
        start, end = raw.find("{"), raw.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(raw[start:end])
            score  = int(result.get("score", 3))
            reason = result.get("reason", "")
            return {"score": score, "reason": reason, "kw_hit": kw_hit}
    except Exception:
        pass

    # 파싱 실패 시 키워드 기반 휴리스틱 점수
    heuristic = min(5, max(1, 2 + kw_hit))
    return {"score": heuristic, "reason": f"파싱 실패 — 키워드 {kw_hit}개 기반 휴리스틱", "kw_hit": kw_hit}


# ── 메인 실행 ─────────────────────────────────────────────────────────────────
def run() -> dict:
    testset = json.loads(TESTSET_PATH.read_text(encoding="utf-8"))
    if not testset:
        print("[LLM] llm_testset.json이 비어 있습니다.")
        return {"avg_score": None, "total": 0}

    claude = ClaudeClient()
    rag    = RAGEngine(collection_name=DEFAULT_COLLECTION_NAME)
    kg     = KnowledgeGraph()

    scores  = []
    details = []
    for item in testset:
        question          = item["question"]
        reference         = item["reference_answer"]
        required_keywords = item.get("required_keywords", [])
        domain            = item.get("domain", "beauty_ecommerce")

        print(f"  [{domain}] {question[:45]}...", flush=True)

        actual = generate_answer(claude, rag, kg, question, domain)
        result = judge_answer(claude, question, reference, required_keywords, actual)

        scores.append(result["score"])
        details.append({
            "question":          question,
            "domain":            domain,
            "score":             result["score"],
            "reason":            result["reason"],
            "kw_hit":            result["kw_hit"],
            "required_keywords": required_keywords,
            "actual":            actual[:300],
        })

    avg = round(sum(scores) / len(scores), 2) if scores else 0.0
    print(f"\n[LLM] 평균 점수: {avg} / 5.0  ({len(scores)}개 질문)")
    for d in details:
        kw_info = f"키워드 {d['kw_hit']}/{len(d['required_keywords'])}개"
        print(f"  [{d['score']}/5] {kw_info}  {d['question'][:45]}")
        print(f"         → {d['reason']}")

    return {
        "avg_score": avg,
        "total":     len(testset),
        "scores":    scores,
        "details":   details,
    }


if __name__ == "__main__":
    run()
