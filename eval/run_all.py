#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전체 정확도 측정 실행 및 결과 저장
실행: python eval/run_all.py
결과: eval/results.json
"""
import sys
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

RESULTS_PATH = Path(__file__).parent / "results.json"


def _fmt(value, suffix="") -> str:
    if value is None:
        return "측정 불가"
    return f"{value}{suffix}"


def main():
    print("\n" + "=" * 45)
    print("  WorkGraph AI 정확도 측정 시작")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 45 + "\n")

    results = {}

    # 1. RAG Hit Rate@3
    print("[1/4] RAG 검색 정확도 측정...")
    try:
        from eval.test_rag import run as run_rag
        results["rag"] = run_rag()
    except Exception as e:
        print(f"  오류: {e}")
        results["rag"] = {"hit_rate_at_3": None, "error": str(e)}

    print()

    # 2. LLM 답변 품질
    print("[2/4] LLM 답변 품질 측정...")
    try:
        from eval.test_llm import run as run_llm
        results["llm"] = run_llm()
    except Exception as e:
        print(f"  오류: {e}")
        results["llm"] = {"avg_score": None, "error": str(e)}

    print()

    # 3. FK 감지 정확도
    print("[3/4] FK 자동 감지 정확도 측정...")
    try:
        from eval.test_fk import run as run_fk
        results["fk"] = run_fk()
    except Exception as e:
        print(f"  오류: {e}")
        results["fk"] = {"precision": None, "recall": None, "f1": None, "error": str(e)}

    print()

    # 4. 도메인 인식 정확도
    print("[4/4] 도메인 자동 인식 정확도 측정...")
    try:
        from eval.test_domain import run as run_domain
        results["domain"] = run_domain()
    except Exception as e:
        print(f"  오류: {e}")
        results["domain"] = {"accuracy": None, "error": str(e)}

    print()

    # ── 결과 저장 ─────────────────────────────────────────────────────────────
    results["timestamp"] = datetime.now().isoformat()
    RESULTS_PATH.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # ── 최종 출력 ─────────────────────────────────────────────────────────────
    rag_rate    = _fmt(results["rag"].get("hit_rate_at_3"), "%")
    llm_avg     = _fmt(results["llm"].get("avg_score"), " / 5.0")
    fk_prec     = _fmt(results["fk"].get("precision"), "%")
    fk_recall   = _fmt(results["fk"].get("recall"), "%")
    domain_acc  = _fmt(results["domain"].get("accuracy"), "%")

    print("=" * 45)
    print("  === WorkGraph AI 정확도 측정 결과 ===")
    print(f"  RAG Hit Rate@3:       {rag_rate}")
    print(f"  LLM 답변 품질:        {llm_avg}")
    print(f"  FK 감지 Precision:    {fk_prec}")
    print(f"  FK 감지 Recall:       {fk_recall}")
    print(f"  도메인 인식 Accuracy: {domain_acc}")
    print("=" * 45)
    print(f"  결과 저장: {RESULTS_PATH}")
    print("=" * 45 + "\n")


if __name__ == "__main__":
    main()
