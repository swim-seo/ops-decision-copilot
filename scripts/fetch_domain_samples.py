#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase에서 도메인별 테이블 목록과 샘플 데이터(LIMIT 5)를 조회하여
domain_samples.txt에 저장합니다.
"""
import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── 환경변수 로드 ─────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL / SUPABASE_KEY 미설정")
    sys.exit(1)

# 도메인 prefix 매핑 (user 요청 label → Supabase prefix)
DOMAIN_MAP = {
    "beauty_ecommerce": "beauty",
    "supply_chain":     "supply",
    "energy":           "energy",
    "manufacturing":    "manufacturing",
    "logistics":        "logistics",
    "finance":          "finance",
}

HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
}


def get_all_tables() -> list[str]:
    """information_schema.tables에서 public 스키마의 테이블 목록 조회."""
    url = f"{SUPABASE_URL}/rest/v1/rpc/get_tables"
    # PostgREST에서는 information_schema를 직접 조회할 수 없으므로
    # RPC 없이 각 도메인 테이블을 직접 탐색합니다.
    # 대신 known 테이블 목록을 기반으로 존재 여부를 확인합니다.
    pass


def list_tables_for_domain(prefix: str) -> list[str]:
    """
    Supabase REST API로 해당 prefix를 가진 테이블 존재 여부를 확인합니다.
    알려진 테이블 패턴을 시도하고, HTTP 200이면 존재하는 것으로 간주합니다.
    """
    known_patterns = [
        # beauty / supply_chain 공통
        "mst_product", "mst_supplier", "mst_channel", "mst_location",
        "mst_office", "mst_part", "mst_supply_route", "mst_warehouse",
        "fact_monthly_sales", "fact_inventory", "fact_inventory_snapshot",
        "fact_replenishment_order", "fact_stockout_event",
        "fact_monthly_demand", "fact_order",
        # energy
        "mst_region", "mst_plant", "mst_meter",
        "fact_daily_usage", "fact_monthly_bill", "fact_outage",
        # manufacturing
        "mst_line", "mst_equipment",
        "fact_production", "fact_defect", "fact_maintenance",
        # logistics
        "mst_hub", "mst_vehicle", "mst_route",
        "fact_delivery", "fact_delay", "fact_cost",
        # finance
        "mst_customer", "mst_branch",
        "fact_transaction", "fact_risk", "fact_performance",
    ]

    found = []
    for pattern in known_patterns:
        table_name = f"{prefix}_{pattern}"
        url = f"{SUPABASE_URL}/rest/v1/{table_name}?limit=0"
        try:
            r = requests.get(url, headers=HEADERS, timeout=8)
            if r.status_code == 200:
                found.append(table_name)
        except requests.RequestException:
            pass
    return found


def fetch_sample(table_name: str, limit: int = 5) -> list[dict]:
    """테이블에서 LIMIT 개 행을 조회합니다."""
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    params = {"select": "*", "limit": limit}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
        return []
    except requests.RequestException as e:
        return [{"error": str(e)}]


def format_table(rows: list[dict]) -> str:
    """리스트를 보기 좋은 텍스트 테이블로 변환합니다."""
    if not rows:
        return "  (데이터 없음)\n"
    if "error" in rows[0]:
        return f"  ERROR: {rows[0]['error']}\n"

    cols = list(rows[0].keys())
    # 컬럼 너비 계산
    widths = {c: max(len(c), max(len(str(r.get(c, ""))) for r in rows)) for c in cols}
    widths = {c: min(w, 30) for c, w in widths.items()}  # max 30자

    sep = "  +" + "+".join("-" * (widths[c] + 2) for c in cols) + "+"
    header = "  |" + "|".join(f" {c:<{widths[c]}} " for c in cols) + "|"

    lines = [sep, header, sep]
    for row in rows:
        val_line = "  |"
        for c in cols:
            val = str(row.get(c, ""))[:30]
            val_line += f" {val:<{widths[c]}} |"
        lines.append(val_line)
    lines.append(sep)
    return "\n".join(lines) + "\n"


def main():
    output_path = Path(__file__).parent.parent / "domain_samples.txt"
    lines = []

    lines.append("=" * 70)
    lines.append("  Supabase 도메인별 테이블 샘플 데이터")
    lines.append(f"  생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  접속 URL: {SUPABASE_URL}")
    lines.append("=" * 70)
    lines.append("")

    for domain_label, prefix in DOMAIN_MAP.items():
        print(f"\n[{domain_label}] 테이블 탐색 중...", flush=True)

        lines.append("=" * 70)
        lines.append(f"  DOMAIN: {domain_label}  (prefix: {prefix}_)")
        lines.append("=" * 70)
        lines.append("")

        tables = list_tables_for_domain(prefix)

        if not tables:
            lines.append("  ⚠️  테이블 없음 (Supabase에 데이터 미업로드 또는 접근 불가)\n")
            print(f"  → 테이블 없음")
            continue

        lines.append(f"  테이블 목록 ({len(tables)}개):")
        for t in tables:
            lines.append(f"    - {t}")
        lines.append("")

        for table in tables:
            print(f"  → {table} 조회 중...", flush=True)
            lines.append(f"  ── {table} (SELECT * LIMIT 5) ──")
            rows = fetch_sample(table, limit=5)
            lines.append(format_table(rows))

        lines.append("")

    output = "\n".join(lines)
    output_path.write_text(output, encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"  저장 완료: {output_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
