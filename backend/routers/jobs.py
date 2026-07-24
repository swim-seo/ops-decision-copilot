"""[역할] 비동기 잡 상태 조회 라우터 (Sprint 4 ②)."""
from fastapi import APIRouter, HTTPException

from modules import job_queue

router = APIRouter()


@router.get("/{job_id}")
def get_job_status(job_id: str):
    """잡 상태 행을 반환한다(폴링용). status: pending|processing|done|failed."""
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(404, f"잡 없음: {job_id}")
    return job
