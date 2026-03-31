#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FK 자동 감지 정확도 평가 — Precision / Recall / F1
테스트셋: eval/fk_testset.json
실행: python eval/test_fk.py
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from modules.document_parser import extract_csv_schema
from modules.knowledge_graph import KnowledgeGraph

TESTSET_PATH = Path(__file__).parent / "fk_testset.json"
DATA_DIR     = ROOT / "data"


def _load_csv_text(filename: str) -> str:
    path = DATA_DIR / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig")


def detect_fk_edges(files: list[str]) -> set[str]:
    """
    파일 목록에서 FK 엣지를 감지합니다.
    반환: {"TABLE_A.COL_X -> TABLE_B", ...} 형태의 집합
    """
    kg = KnowledgeGraph()
    schemas = []
    table_names = []

    for fname in files:
        raw = _load_csv_text(fname)
        if not raw:
            continue
        schema = extract_csv_schema(fname, raw)
        schemas.append(schema)
        table_names.append(schema["table_name"])

    # 1-pass: 모든 테이블 노드 추가
    for schema in schemas:
        kg.build_from_csv_schema(schema, all_table_names=table_names)

    # 감지된 엣지 수집
    edges = set()
    for src, tgt, data in kg.graph.edges(data=True):
        fk_col = data.get("relation", "")
        edge_str = f"{src}.{fk_col} -> {tgt}".upper()
        edges.add(edge_str)

    return edges


def _normalize_edge(edge: list) -> str:
    """
    ["FACT_SALES.PRODUCT_ID", "MST_PRODUCT.PRODUCT_ID"]
    → "FACT_SALES.PRODUCT_ID -> MST_PRODUCT" (테이블 기준)
    """
    src_full = edge[0].upper()   # TABLE.COL
    tgt_full = edge[1].upper()   # TABLE.COL
    tgt_table = tgt_full.split(".")[0]
    return f"{src_full} -> {tgt_table}"


def run() -> dict:
    testset = json.loads(TESTSET_PATH.read_text(encoding="utf-8"))
    if not testset:
        print("[FK] fk_testset.json이 비어 있습니다.")
        return {"precision": None, "recall": None, "f1": None}

    tp_total = fp_total = fn_total = 0
    details = []

    for item in testset:
        files    = item["files"]
        expected = {_normalize_edge(e) for e in item["expected_edges"]}
        detected = detect_fk_edges(files)

        tp = len(expected & detected)
        fp = len(detected - expected)
        fn = len(expected - detected)

        tp_total += tp
        fp_total += fp
        fn_total += fn

        details.append({
            "files":    files,
            "expected": list(expected),
            "detected": list(detected),
            "tp": tp, "fp": fp, "fn": fn,
        })

    precision = round(tp_total / (tp_total + fp_total) * 100, 1) if (tp_total + fp_total) > 0 else 0.0
    recall    = round(tp_total / (tp_total + fn_total) * 100, 1) if (tp_total + fn_total) > 0 else 0.0
    f1 = round(2 * precision * recall / (precision + recall), 1) if (precision + recall) > 0 else 0.0

    print(f"[FK] Precision: {precision}%  Recall: {recall}%  F1: {f1}%")
    for d in details:
        print(f"  파일: {d['files']}")
        print(f"    정답: {d['expected']}")
        print(f"    감지: {d['detected']}")
        print(f"    TP={d['tp']} FP={d['fp']} FN={d['fn']}")

    return {
        "precision": precision,
        "recall":    recall,
        "f1":        f1,
        "tp": tp_total, "fp": fp_total, "fn": fn_total,
        "details": details,
    }


if __name__ == "__main__":
    run()
