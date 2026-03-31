#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG 검색 정확도 평가 — Hit Rate@3 측정
테스트셋: eval/rag_testset.json (Q&A 쌍 20개)
실행: python eval/test_rag.py
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from modules.rag_engine import RAGEngine
from config import DEFAULT_COLLECTION_NAME

TESTSET_PATH = Path(__file__).parent / "rag_testset.json"
TOP_K = 3


def run() -> dict:
    testset = json.loads(TESTSET_PATH.read_text(encoding="utf-8"))
    if not testset:
        print("[RAG] rag_testset.json이 비어 있습니다.")
        return {"hit_rate_at_3": None, "hits": 0, "total": 0}

    rag = RAGEngine(collection_name=DEFAULT_COLLECTION_NAME)

    if rag.document_count() == 0:
        print("[RAG] ChromaDB에 문서가 없습니다. 먼저 앱에서 문서를 업로드하세요.")
        return {"hit_rate_at_3": None, "hits": 0, "total": len(testset)}

    hits = 0
    details = []
    for item in testset:
        question = item["question"]
        expected = item["expected_source"].lower()

        results = rag.query(question, n_results=TOP_K)
        found_sources = [r["filename"].lower() for r in results]

        matched = any(expected in src or src in expected for src in found_sources)
        if matched:
            hits += 1

        details.append({
            "question":  question,
            "expected":  expected,
            "retrieved": found_sources,
            "hit":       matched,
        })

    total = len(testset)
    hit_rate = round(hits / total * 100, 1) if total > 0 else 0.0

    print(f"[RAG] Hit Rate@{TOP_K}: {hit_rate}%  ({hits}/{total})")
    for d in details:
        mark = "O" if d["hit"] else "X"
        print(f"  [{mark}] {d['question']}")
        if not d["hit"]:
            print(f"       expected: {d['expected']}")
            print(f"       got:      {d['retrieved']}")

    return {
        "hit_rate_at_3": hit_rate,
        "hits":  hits,
        "total": total,
        "details": details,
    }


if __name__ == "__main__":
    run()
