"""
[역할] Supabase PostgreSQL 연결 클라이언트 (REST API 경량 방식)
  - is_connected()     : 연결 상태 확인
  - query_table()      : 테이블 전체 조회 → pandas DataFrame
  - upsert_dataframe() : DataFrame → Supabase 테이블 업로드
  - get_status()       : 연결 상태 정보 반환

supabase-py 패키지 없이 REST API로 직접 통신합니다.
연결 실패 시 CSV fallback 모드로 자동 전환됩니다.
"""
import json
import logging
import math
from typing import Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)

# ── 싱글톤 상태 ──────────────────────────────────────────────────────────────
_url: str = ""
_key: str = ""
_connected: Optional[bool] = None
_error_msg: str = ""


def _get_credentials() -> tuple:
    from config import _get_secret
    return _get_secret("SUPABASE_URL"), _get_secret("SUPABASE_KEY")


def _headers() -> dict:
    return {
        "apikey": _key,
        "Authorization": f"Bearer {_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }


def _init():
    """최초 연결 확인. 한 번만 실행됩니다."""
    global _url, _key, _connected, _error_msg
    if _connected is not None:
        return

    _url, _key = _get_credentials()
    if not _url or not _key:
        _connected = False
        _error_msg = "SUPABASE_URL 또는 SUPABASE_KEY 미설정"
        return

    # 연결 테스트: 임의 테이블 조회 → 인증 성공 여부 확인
    try:
        r = requests.get(
            f"{_url}/rest/v1/?limit=0",
            headers=_headers(),
            timeout=5,
        )
        if r.status_code in (200, 404):
            _connected = True
            _error_msg = ""
            logger.info("Supabase connected via REST API")
        elif r.status_code in (401, 403):
            _connected = False
            _error_msg = f"Supabase 인증 실패 (HTTP {r.status_code})"
        else:
            _connected = False
            _error_msg = f"Supabase 응답 오류 (HTTP {r.status_code})"
    except requests.RequestException as e:
        _connected = False
        _error_msg = f"Supabase 연결 실패: {e}"


def is_connected() -> bool:
    _init()
    return bool(_connected)


def get_status() -> dict:
    _init()
    return {
        "connected": bool(_connected),
        "mode": "Supabase" if _connected else "CSV (로컬)",
        "error": _error_msg,
    }


def query_table(table_name: str) -> Optional[pd.DataFrame]:
    """Supabase 테이블에서 전체 데이터를 조회합니다."""
    _init()
    if not _connected:
        return None

    try:
        all_rows = []
        page_size = 1000
        offset = 0
        while True:
            r = requests.get(
                f"{_url}/rest/v1/{table_name}",
                headers={**_headers(), "Range": f"{offset}-{offset + page_size - 1}"},
                params={"select": "*"},
                timeout=15,
            )
            if r.status_code == 404 or r.status_code == 406:
                return None
            r.raise_for_status()
            rows = r.json()
            if not rows:
                break
            all_rows.extend(rows)
            if len(rows) < page_size:
                break
            offset += page_size

        if not all_rows:
            return None
        return pd.DataFrame(all_rows)
    except Exception as e:
        logger.debug("Supabase query failed for %s: %s", table_name, e)
        return None


def upsert_dataframe(table_name: str, df: pd.DataFrame, chunk_size: int = 500) -> int:
    """DataFrame을 Supabase 테이블에 upsert합니다."""
    _init()
    if not _connected:
        raise ConnectionError("Supabase에 연결되지 않았습니다.")

    # NaN/NaT → None
    records = df.to_dict(orient="records")
    for rec in records:
        for k, v in rec.items():
            if v is None:
                continue
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                rec[k] = None
            elif pd.isna(v):
                rec[k] = None

    total = 0
    headers = {**_headers(), "Prefer": "resolution=merge-duplicates"}

    for i in range(0, len(records), chunk_size):
        chunk = records[i:i + chunk_size]
        r = requests.post(
            f"{_url}/rest/v1/{table_name}",
            headers=headers,
            data=json.dumps(chunk, ensure_ascii=False, default=str),
            timeout=30,
        )
        if r.status_code not in (200, 201, 204):
            raise RuntimeError(f"Upsert failed for {table_name} (chunk {i}): {r.text}")
        total += len(chunk)

    return total
