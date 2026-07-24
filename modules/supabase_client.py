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


def delete_rows(table_name: str, filters: dict) -> None:
    """조건에 맞는 행을 삭제합니다. filters = {"col": "eq.value", ...}"""
    _init()
    if not _connected:
        return
    try:
        requests.delete(
            f"{_url}/rest/v1/{table_name}",
            headers=_headers(),
            params=filters,
            timeout=15,
        )
    except Exception as e:
        logger.debug("Supabase delete_rows failed for %s: %s", table_name, e)


def rpc(function_name: str, params: dict) -> Optional[list]:
    """Supabase RPC 함수를 호출합니다."""
    _init()
    if not _connected:
        return None
    try:
        r = requests.post(
            f"{_url}/rest/v1/rpc/{function_name}",
            headers=_headers(),
            json=params,
            timeout=15,
        )
        if r.status_code == 200:
            return r.json()
        logger.debug("Supabase rpc %s failed (HTTP %s): %s", function_name, r.status_code, r.text)
        return None
    except Exception as e:
        logger.debug("Supabase rpc failed for %s: %s", function_name, e)
        return None


def count_rows(table_name: str, filters: dict) -> int:
    """조건에 맞는 행 수를 반환합니다."""
    _init()
    if not _connected:
        return 0
    try:
        r = requests.get(
            f"{_url}/rest/v1/{table_name}",
            headers={**_headers(), "Prefer": "count=exact"},
            params={"select": "id", **filters},
            timeout=10,
        )
        content_range = r.headers.get("Content-Range", "*/0")
        return int(content_range.split("/")[-1])
    except Exception:
        return 0


def select_one(table_name: str, filters: dict) -> Optional[dict]:
    """단일 행을 조회합니다. filters = {"col": "eq.value"}. 없으면 None.

    query_table()이 테이블 전체를 DataFrame으로 가져오는 것과 달리,
    PK 등으로 한 행만 필요할 때 쓰는 경량 조회입니다(예: KG blob 로드).
    """
    _init()
    if not _connected:
        return None
    try:
        r = requests.get(
            f"{_url}/rest/v1/{table_name}",
            headers=_headers(),
            params={"select": "*", "limit": "1", **filters},
            timeout=15,
        )
        if r.status_code != 200:
            return None
        rows = r.json()
        return rows[0] if rows else None
    except Exception as e:
        logger.debug("Supabase select_one failed for %s: %s", table_name, e)
        return None


def update_rows(table_name: str, filters: dict, patch: dict) -> bool:
    """조건에 맞는 행을 부분 갱신(PATCH)합니다. filters={"col":"eq.val"}. 성공 여부 반환.

    upsert 와 달리 지정한 컬럼만 갱신하고 나머지는 보존한다(잡 상태 전이 등에 적합).
    """
    _init()
    if not _connected:
        return False
    try:
        r = requests.patch(
            f"{_url}/rest/v1/{table_name}",
            headers=_headers(),
            params=filters,
            data=json.dumps(patch, ensure_ascii=False, default=str),
            timeout=30,
        )
        if r.status_code in (200, 204):
            return True
        logger.error("Supabase update 실패 (%s, HTTP %s): %s", table_name, r.status_code, r.text)
        return False
    except Exception as e:
        logger.debug("Supabase update_rows failed for %s: %s", table_name, e)
        return False


def upsert_rows(table_name: str, records: list) -> bool:
    """레코드(list[dict])를 PK 기준 upsert합니다. 성공 여부를 반환합니다.

    upsert_dataframe()의 dict 버전 — DataFrame 없이 소량의 임의 JSON(중첩
    jsonb 포함)을 바로 넣을 때 사용합니다(예: KG node_link_data blob).
    """
    _init()
    if not _connected:
        return False
    if not records:
        return True
    try:
        headers = {**_headers(), "Prefer": "resolution=merge-duplicates"}
        r = requests.post(
            f"{_url}/rest/v1/{table_name}",
            headers=headers,
            data=json.dumps(records, ensure_ascii=False, default=str),
            timeout=30,
        )
        if r.status_code in (200, 201, 204):
            return True
        logger.error("Supabase upsert 실패 (%s, HTTP %s): %s", table_name, r.status_code, r.text)
        return False
    except Exception as e:
        logger.debug("Supabase upsert_rows failed for %s: %s", table_name, e)
        return False


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
