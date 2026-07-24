"""
[역할] 비동기 잡 큐 — Supabase jobs 테이블 접근 (Sprint 4 ②)

업로드/KG빌드처럼 오래 걸리는 작업을 요청에서 분리한다. 요청은 잡을 enqueue 하고
즉시 job_id 를 받고, 워커(modules/worker.py)가 백그라운드로 처리한다.

경쟁 안전 클레임은 Postgres RPC claim_next_job() 에 위임한다(PostgREST 는 SELECT
FOR UPDATE 를 직접 못 함 — scripts/jobs_migration.sql 참고).

상태: pending → processing(claim) → done | failed. 실패 시 attempts<max 면 pending
으로 되돌려 재시도.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import modules.supabase_client as _sb

logger = logging.getLogger(__name__)

_TABLE = "jobs"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def enqueue(job_type: str, payload: dict, max_attempts: int = 3) -> Optional[str]:
    """잡을 큐에 넣고 job_id 를 반환한다. 실패(미연결 등)면 None."""
    job_id = uuid.uuid4().hex
    ok = _sb.upsert_rows(_TABLE, [{
        "id":           job_id,
        "job_type":     job_type,
        "payload":      payload,
        "status":       "pending",
        "attempts":     0,
        "max_attempts": max_attempts,
    }])
    if not ok:
        logger.error("잡 enqueue 실패: type=%s", job_type)
        return None
    logger.info("잡 enqueue: %s (type=%s)", job_id, job_type)
    return job_id


def claim_next(lease_seconds: int = 300) -> Optional[dict]:
    """다음 잡을 원자적으로 집어 processing 으로 전환한다(RPC). 없으면 None."""
    rows = _sb.rpc("claim_next_job", {"lease_seconds": lease_seconds})
    return rows[0] if rows else None


def complete(job_id: str, result: Any) -> None:
    """잡을 완료(done) 처리하고 결과를 기록한다."""
    _sb.update_rows(_TABLE, {"id": f"eq.{job_id}"}, {
        "status":      "done",
        "result":      result,
        "error":       None,
        "finished_at": _now_iso(),
    })


def fail(job_id: str, error: str, attempts: int, max_attempts: int) -> None:
    """잡 실패 처리. attempts<max 면 pending 으로 되돌려 재시도, 아니면 failed 확정."""
    if attempts < max_attempts:
        # 재시도 — started_at 은 남겨두되 pending 으로(다음 claim 대상). 마지막 에러 기록.
        _sb.update_rows(_TABLE, {"id": f"eq.{job_id}"}, {
            "status": "pending",
            "error":  error[:2000],
        })
        logger.warning("잡 재시도 예약: %s (attempt %d/%d)", job_id, attempts, max_attempts)
    else:
        _sb.update_rows(_TABLE, {"id": f"eq.{job_id}"}, {
            "status":      "failed",
            "error":       error[:2000],
            "finished_at": _now_iso(),
        })
        logger.error("잡 실패 확정: %s (attempts %d)", job_id, attempts)


def get_job(job_id: str) -> Optional[dict]:
    """잡 상태 행을 반환한다(폴링용). 없으면 None."""
    return _sb.select_one(_TABLE, {"id": f"eq.{job_id}"})
