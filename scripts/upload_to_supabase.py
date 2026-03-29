#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[역할] data/ 폴더의 CSV 파일을 Supabase PostgreSQL 테이블로 업로드

사용법:
  python scripts/upload_to_supabase.py              # 전체 업로드
  python scripts/upload_to_supabase.py --table FACT_MONTHLY_SALES  # 특정 테이블만
  python scripts/upload_to_supabase.py --create-sql  # CREATE TABLE SQL만 출력

사전 준비:
  1. Supabase 프로젝트 생성 (https://supabase.com)
  2. .env 또는 .streamlit/secrets.toml에 SUPABASE_URL, SUPABASE_KEY 설정
  3. Supabase SQL Editor에서 아래 --create-sql 출력을 실행하여 테이블 생성
  4. 이 스크립트 실행하여 데이터 업로드

주의:
  - Supabase REST API는 upsert를 사용합니다 (기존 데이터 덮어쓰기)
  - 대량 데이터는 500행씩 분할 업로드합니다
  - 테이블은 미리 Supabase SQL Editor에서 생성해야 합니다
"""
import os
import sys

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# ── CSV 파일명 → 테이블명 매핑 ──────────────────────────────────────────────
def csv_to_table(filename: str) -> str:
    return filename.replace(".csv", "").replace(".CSV", "").lower()


# ── pandas dtype → PostgreSQL 타입 매핑 ─────────────────────────────────────
def _pg_type(dtype, col_name: str) -> str:
    s = str(dtype)
    col_upper = col_name.upper()

    # ID/코드 컬럼은 항상 TEXT
    if any(k in col_upper for k in ["_ID", "_CD", "_NO", "_KEY", "_CODE", "STATUS",
                                      "NAME", "TYPE", "REGION", "COUNTRY", "CATEGORY",
                                      "DESCRIPTION", "CAUSE", "STAGE", "PEAK"]):
        return "TEXT"
    # 날짜 컬럼
    if any(k in col_upper for k in ["DATE", "YEAR_MONTH", "LAUNCH", "_DT", "_YM"]):
        return "TEXT"  # YYYY-MM 형식은 TEXT가 안전
    if "int" in s:
        return "BIGINT"
    if "float" in s:
        return "DOUBLE PRECISION"
    return "TEXT"


def _detect_pk(df: pd.DataFrame, table_name: str) -> list:
    """주요 키 컬럼 추정"""
    cols = [c.upper() for c in df.columns]
    candidates = []

    # FACT 테이블: 복합 키
    if "fact" in table_name:
        for c in df.columns:
            cu = c.upper()
            if any(k in cu for k in ["_ID", "_CD", "YEAR_MONTH", "SNAPSHOT_DATE",
                                       "ORDER_DT", "STOCKOUT_YM"]):
                candidates.append(c)
        return candidates[:3] if candidates else [df.columns[0]]

    # MST 테이블: 단일 키
    for c in df.columns:
        cu = c.upper()
        if cu.endswith("_ID") or cu.endswith("_CD"):
            return [c]

    return [df.columns[0]]


# ── CREATE TABLE SQL 생성 ──────────────────────────────────────────────────
def generate_create_sql(csv_path: Path) -> str:
    df = pd.read_csv(csv_path, encoding="utf-8-sig", nrows=100)
    table_name = csv_to_table(csv_path.name)
    pk_cols = _detect_pk(df, table_name)

    lines = [f"DROP TABLE IF EXISTS {table_name} CASCADE;"]
    lines.append(f"CREATE TABLE {table_name} (")
    col_defs = []
    for col in df.columns:
        pg_type = _pg_type(df[col].dtype, col)
        # 대문자 컬럼명은 따옴표로 감싸서 PostgreSQL이 대소문자 유지
        col_defs.append(f'  "{col}" {pg_type}')

    lines.append(",\n".join(col_defs))

    if pk_cols:
        pk_str = ", ".join(f'"{c}"' for c in pk_cols)
        lines.append(f"  , PRIMARY KEY ({pk_str})")

    lines.append(");")
    lines.append("")
    lines.append(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;")
    lines.append(f'CREATE POLICY "Allow all" ON {table_name}')
    lines.append(f"  FOR ALL USING (true) WITH CHECK (true);")
    lines.append("")

    return "\n".join(lines)


# ── 업로드 ──────────────────────────────────────────────────────────────────
def upload_csv(csv_path: Path, dry_run: bool = False) -> dict:
    """단일 CSV를 Supabase에 업로드합니다."""
    from modules.supabase_client import upsert_dataframe, is_connected

    if not is_connected():
        return {"file": csv_path.name, "status": "error", "message": "Supabase 연결 실패"}

    table_name = csv_to_table(csv_path.name)
    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    if dry_run:
        return {
            "file": csv_path.name,
            "table": table_name,
            "rows": len(df),
            "columns": list(df.columns),
            "status": "dry_run",
        }

    try:
        count = upsert_dataframe(table_name, df)
        return {
            "file": csv_path.name,
            "table": table_name,
            "rows": count,
            "status": "success",
        }
    except Exception as e:
        return {
            "file": csv_path.name,
            "table": table_name,
            "status": "error",
            "message": str(e),
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CSV → Supabase 업로드")
    parser.add_argument("--table", help="특정 테이블만 업로드 (예: FACT_MONTHLY_SALES)")
    parser.add_argument("--create-sql", action="store_true", help="CREATE TABLE SQL만 출력")
    parser.add_argument("--dry-run", action="store_true", help="실제 업로드 없이 미리보기")
    args = parser.parse_args()

    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        print(f"CSV 파일이 없습니다: {DATA_DIR}")
        sys.exit(1)

    if args.table:
        target = args.table.upper()
        csv_files = [f for f in csv_files if target in f.stem.upper()]
        if not csv_files:
            print(f"'{args.table}' 에 해당하는 CSV 파일을 찾을 수 없습니다.")
            sys.exit(1)

    # CREATE TABLE SQL 출력 모드
    if args.create_sql:
        print("-- " + "=" * 57)
        print("-- Supabase SQL Editor에서 실행하세요")
        print("-- " + "=" * 57)
        print()
        for csv_path in csv_files:
            print(f"-- {csv_path.name}")
            print(generate_create_sql(csv_path))
            print()
        return

    # 업로드 모드
    print(f"\n{'=' * 60}")
    print(f"  CSV → Supabase 업로드 {'(DRY RUN)' if args.dry_run else ''}")
    print(f"  대상: {len(csv_files)}개 파일")
    print(f"{'=' * 60}\n")

    results = []
    for csv_path in csv_files:
        print(f"  [{csv_path.name}] ", end="", flush=True)
        result = upload_csv(csv_path, dry_run=args.dry_run)
        results.append(result)

        if result["status"] == "success":
            print(f"OK {result['rows']} rows uploaded")
        elif result["status"] == "dry_run":
            print(f"   {result['rows']} rows, {len(result['columns'])} cols")
        else:
            print(f"FAIL {result.get('message', 'unknown error')}")

    # 결과 요약
    success = sum(1 for r in results if r["status"] == "success")
    errors = sum(1 for r in results if r["status"] == "error")
    print(f"\n{'=' * 60}")
    print(f"  Done: success {success} / fail {errors} / total {len(results)}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
