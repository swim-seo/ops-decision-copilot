#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[역할] 도메인별 CSV 데이터를 Supabase에 접두어(prefix) 붙여 업로드

사용법:
  python scripts/upload_all_domains.py              # 전체 업로드
  python scripts/upload_all_domains.py --domain beauty   # 특정 도메인만
  python scripts/upload_all_domains.py --create-sql      # SQL만 출력
  python scripts/upload_all_domains.py --dry-run         # 미리보기

업로드 테이블명:
  beauty_mst_product, supply_mst_part, energy_mst_plant, ...
"""
import os
import sys
import argparse
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── 도메인 → (서브디렉터리, 테이블 목록) 매핑 ─────────────────────────────
DOMAIN_CONFIG = {
    "beauty": {
        "dir":    Path("data"),
        "tables": ["MST_SUPPLIER","MST_CHANNEL","MST_PRODUCT","MST_LOCATION",
                   "FACT_MONTHLY_SALES","FACT_INVENTORY",
                   "MST_OFFICE","MST_PART","MST_SUPPLY_ROUTE",
                   "FACT_REPLENISHMENT_ORDER","FACT_STOCKOUT_EVENT"],
    },
    "supply": {
        "dir":    Path("data/supply_chain"),
        "tables": ["MST_PART","MST_SUPPLIER","MST_WAREHOUSE",
                   "FACT_MONTHLY_DEMAND","FACT_INVENTORY","FACT_ORDER"],
    },
    "energy": {
        "dir":    Path("data/energy"),
        "tables": ["MST_REGION","MST_PLANT","MST_METER",
                   "FACT_DAILY_USAGE","FACT_MONTHLY_BILL","FACT_OUTAGE"],
    },
    "manufacturing": {
        "dir":    Path("data/manufacturing"),
        "tables": ["MST_LINE","MST_EQUIPMENT","MST_PRODUCT",
                   "FACT_PRODUCTION","FACT_DEFECT","FACT_MAINTENANCE"],
    },
    "logistics": {
        "dir":    Path("data/logistics"),
        "tables": ["MST_HUB","MST_VEHICLE","MST_ROUTE",
                   "FACT_DELIVERY","FACT_DELAY","FACT_COST"],
    },
    "finance": {
        "dir":    Path("data/finance"),
        "tables": ["MST_PRODUCT","MST_CUSTOMER","MST_BRANCH",
                   "FACT_TRANSACTION","FACT_RISK","FACT_PERFORMANCE"],
    },
}

PROJECT_ROOT = Path(__file__).parent.parent


def _pg_type(dtype, col_name: str) -> str:
    s = str(dtype)
    cu = col_name.upper()
    if any(k in cu for k in ["_ID","_CD","_NO","_KEY","_CODE","STATUS","NAME",
                              "TYPE","REGION","CATEGORY","DESCRIPTION","CAUSE",
                              "STAGE","PEAK","REASON","FLAG","GRADE","CHANNEL"]):
        return "TEXT"
    if any(k in cu for k in ["DATE","YEAR_MONTH","LAUNCH","_DT","_YM","TIME"]):
        return "TEXT"
    if "int" in s:
        return "BIGINT"
    if "float" in s:
        return "DOUBLE PRECISION"
    return "TEXT"


def _detect_pk(df: pd.DataFrame, table_name: str) -> list:
    cols = list(df.columns)
    if "fact" in table_name.lower():
        cands = [c for c in cols
                 if any(k in c.upper() for k in ["_ID","_CD","YEAR_MONTH",
                                                   "DATE","ORDER_DT","SNAPSHOT"])]
        return cands[:3] if cands else [cols[0]]
    for c in cols:
        cu = c.upper()
        if cu.endswith("_ID") or cu.endswith("_CD"):
            return [c]
    return [cols[0]]


def generate_create_sql(csv_path: Path, prefixed_table: str) -> str:
    df = pd.read_csv(csv_path, encoding="utf-8-sig", nrows=100)
    pk_cols = _detect_pk(df, prefixed_table)

    lines = [f'DROP TABLE IF EXISTS "{prefixed_table}" CASCADE;',
             f'CREATE TABLE "{prefixed_table}" (']
    col_defs = [f'  "{col}" {_pg_type(df[col].dtype, col)}' for col in df.columns]
    lines.append(",\n".join(col_defs))
    if pk_cols:
        pk_str = ", ".join(f'"{c}"' for c in pk_cols)
        lines.append(f"  , PRIMARY KEY ({pk_str})")
    lines.append(");")
    lines.append(f'ALTER TABLE "{prefixed_table}" ENABLE ROW LEVEL SECURITY;')
    lines.append(f'CREATE POLICY "Allow all" ON "{prefixed_table}" FOR ALL USING (true) WITH CHECK (true);')
    lines.append("")
    return "\n".join(lines)


def upload_domain(domain: str, dry_run: bool = False) -> list:
    from modules.supabase_client import upsert_dataframe, is_connected
    cfg = DOMAIN_CONFIG[domain]
    data_dir = PROJECT_ROOT / cfg["dir"]
    results = []

    if not data_dir.exists():
        print(f"  [SKIP] {domain}: 디렉터리 없음 ({data_dir})")
        return results

    for tbl in cfg["tables"]:
        csv_path = data_dir / f"{tbl}.csv"
        if not csv_path.exists():
            results.append({"domain": domain, "table": tbl, "status": "missing"})
            continue

        prefixed = f"{domain}_{tbl.lower()}"
        try:
            df = pd.read_csv(csv_path, encoding="utf-8-sig")
        except Exception as e:
            results.append({"domain": domain, "table": prefixed, "status": "error", "msg": str(e)})
            continue

        if dry_run:
            results.append({"domain": domain, "table": prefixed,
                            "rows": len(df), "cols": len(df.columns), "status": "dry_run"})
            continue

        if not is_connected():
            results.append({"domain": domain, "table": prefixed,
                            "status": "error", "msg": "Supabase 연결 실패"})
            continue

        try:
            count = upsert_dataframe(prefixed, df)
            results.append({"domain": domain, "table": prefixed,
                            "rows": count, "status": "success"})
        except Exception as e:
            results.append({"domain": domain, "table": prefixed,
                            "status": "error", "msg": str(e)})
    return results


def main():
    parser = argparse.ArgumentParser(description="도메인별 CSV → Supabase 업로드 (domain_table 접두어)")
    parser.add_argument("--domain", choices=list(DOMAIN_CONFIG.keys()),
                        help="특정 도메인만 업로드")
    parser.add_argument("--create-sql", action="store_true", help="CREATE TABLE SQL 출력 후 종료")
    parser.add_argument("--dry-run",    action="store_true", help="실제 업로드 없이 미리보기")
    args = parser.parse_args()

    domains = [args.domain] if args.domain else list(DOMAIN_CONFIG.keys())

    # ── CREATE SQL 출력 모드 ──────────────────────────────────────────────────
    if args.create_sql:
        print("-- " + "=" * 60)
        print("-- Supabase SQL Editor에서 실행하세요")
        print("-- " + "=" * 60)
        for domain in domains:
            cfg = DOMAIN_CONFIG[domain]
            data_dir = PROJECT_ROOT / cfg["dir"]
            print(f"\n-- ===== {domain.upper()} =====")
            for tbl in cfg["tables"]:
                csv_path = data_dir / f"{tbl}.csv"
                if csv_path.exists():
                    prefixed = f"{domain}_{tbl.lower()}"
                    print(f"\n-- {tbl} → {prefixed}")
                    print(generate_create_sql(csv_path, prefixed))
        return

    # ── 업로드 모드 ───────────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"  도메인별 CSV → Supabase 업로드 {'(DRY RUN)' if args.dry_run else ''}")
    print(f"  대상 도메인: {', '.join(domains)}")
    print(f"{'='*65}\n")

    all_results = []
    for domain in domains:
        print(f"\n[{domain.upper()}]")
        results = upload_domain(domain, dry_run=args.dry_run)
        for r in results:
            if r["status"] == "success":
                print(f"  ✅ {r['table']:<40} {r['rows']:,} rows")
            elif r["status"] == "dry_run":
                print(f"  🔍 {r['table']:<40} {r['rows']:,} rows, {r['cols']} cols")
            elif r["status"] == "missing":
                print(f"  ⚠️  {domain}_{r['table'].lower():<36} CSV 없음")
            else:
                print(f"  ❌ {r.get('table', r.get('table')):<40} {r.get('msg','')}")
        all_results.extend(results)

    success = sum(1 for r in all_results if r["status"] == "success")
    errors  = sum(1 for r in all_results if r["status"] == "error")
    missing = sum(1 for r in all_results if r["status"] == "missing")

    print(f"\n{'='*65}")
    print(f"  완료: 성공 {success} / 오류 {errors} / 누락 {missing} / 전체 {len(all_results)}")
    print(f"{'='*65}\n")

    if not args.dry_run and success == 0 and errors > 0:
        print("⚠️  Supabase SQL Editor에서 먼저 CREATE TABLE을 실행하세요:")
        print("   python scripts/upload_all_domains.py --create-sql")


if __name__ == "__main__":
    main()
