"""
[역할] Supabase PostgreSQL 연결 클라이언트
  - get_client()       : Supabase 클라이언트 싱글톤 반환
  - is_connected()     : 연결 상태 확인
  - query_table()      : 테이블 전체 조회 → pandas DataFrame
  - table_exists()     : 테이블 존재 여부 확인
  - upsert_dataframe() : DataFrame → Supabase 테이블 업로드

연결 실패 시 CSV fallback 모드로 자동 전환됩니다.
"""
import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ── 싱글톤 상태 ──────────────────────────────────────────────────────────────
_client = None
_connected: Optional[bool] = None  # None=미확인, True/False=확인됨
_error_msg: str = ""


def _get_credentials() -> tuple:
    """SUPABASE_URL, SUPABASE_KEY를 반환합니다."""
    from config import _get_secret
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_KEY")
    return url, key


def get_client():
    """Supabase 클라이언트 싱글톤. 연결 불가 시 None 반환."""
    global _client, _connected, _error_msg
    if _connected is not None:
        return _client

    url, key = _get_credentials()
    if not url or not key:
        _connected = False
        _error_msg = "SUPABASE_URL 또는 SUPABASE_KEY가 설정되지 않았습니다."
        logger.info("Supabase credentials not found — CSV fallback mode")
        return None

    try:
        from supabase import create_client
        _client = create_client(url, key)
        # 연결 확인: 간단한 쿼리
        _client.table("_health_check_dummy").select("*").limit(0).execute()
        _connected = True
        _error_msg = ""
        logger.info("Supabase connected successfully")
    except ImportError:
        _connected = False
        _error_msg = "supabase 패키지가 설치되지 않았습니다. pip install supabase"
        logger.warning(_error_msg)
        _client = None
    except Exception as e:
        # 테이블이 없어도 연결 자체는 성공 (404는 OK, 401/network error는 실패)
        err_str = str(e)
        if "404" in err_str or "relation" in err_str.lower():
            _connected = True
            _error_msg = ""
            logger.info("Supabase connected (health check table not found, but connection OK)")
        elif "401" in err_str or "403" in err_str:
            _connected = False
            _error_msg = f"Supabase 인증 실패: {e}"
            logger.warning(_error_msg)
            _client = None
        else:
            _connected = False
            _error_msg = f"Supabase 연결 실패: {e}"
            logger.warning(_error_msg)
            _client = None

    return _client


def is_connected() -> bool:
    """Supabase 연결 여부 반환. 최초 호출 시 연결을 시도합니다."""
    if _connected is None:
        get_client()
    return bool(_connected)


def get_status() -> dict:
    """연결 상태 정보를 반환합니다."""
    if _connected is None:
        get_client()
    return {
        "connected": bool(_connected),
        "mode": "Supabase" if _connected else "CSV (로컬)",
        "error": _error_msg,
    }


def query_table(table_name: str) -> Optional[pd.DataFrame]:
    """Supabase 테이블에서 전체 데이터를 조회합니다.
    연결 실패 또는 테이블 없으면 None 반환.
    """
    client = get_client()
    if client is None:
        return None

    try:
        # Supabase REST API는 기본 1000행 제한 → 페이지네이션
        all_rows = []
        page_size = 1000
        offset = 0
        while True:
            response = (
                client.table(table_name)
                .select("*")
                .range(offset, offset + page_size - 1)
                .execute()
            )
            rows = response.data
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


def table_exists(table_name: str) -> bool:
    """테이블이 존재하고 조회 가능한지 확인합니다."""
    client = get_client()
    if client is None:
        return False
    try:
        response = client.table(table_name).select("*").limit(1).execute()
        return True
    except Exception:
        return False


def upsert_dataframe(table_name: str, df: pd.DataFrame, chunk_size: int = 500) -> int:
    """DataFrame을 Supabase 테이블에 upsert합니다.
    Returns: 업로드된 행 수. 실패 시 0.
    """
    client = get_client()
    if client is None:
        raise ConnectionError("Supabase에 연결되지 않았습니다.")

    # NaN → None 변환 (JSON 직렬화 호환)
    records = df.where(df.notna(), None).to_dict(orient="records")
    total = 0

    for i in range(0, len(records), chunk_size):
        chunk = records[i:i + chunk_size]
        try:
            client.table(table_name).upsert(chunk).execute()
            total += len(chunk)
        except Exception as e:
            logger.error("Upsert failed for %s (chunk %d): %s", table_name, i, e)
            raise

    return total
