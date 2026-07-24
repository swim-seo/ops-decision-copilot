"""
[역할] 비동기 잡 워커 — 큐를 폴링해 잡을 처리 (Sprint 4 ②)

잡 타입별 핸들러를 레지스트리에 등록해 두고, poll_loop 가 claim_next() 로 잡을
하나씩 집어 실행한다. 성공 시 complete(), 예외 시 fail()(재시도/실패 확정).

실행 모델(Codex Q2):
  - embedded : FastAPI startup 에서 백그라운드 스레드로 poll_loop 실행(데모 기본).
               한 프로세스에서 "그냥 돎". main.py 가 start_embedded_worker() 호출.
  - standalone: `python -m modules.worker` 로 독립 폴러 실행(수평 확장 패턴).
둘은 같은 claim RPC 를 공유하므로 코드 재설계 없이 전환된다.
주의: uvicorn 멀티워커 + embedded 면 프로세스마다 폴러가 돈다. DB 락으로 클레임은
안전하나 부하가 늘 수 있어, 데모는 단일 프로세스(또는 WORKER_EMBEDDED 로 게이트).
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable

from modules import job_queue

logger = logging.getLogger(__name__)

# job_type → 핸들러(payload dict → result). 라우터/모듈이 import 시 등록한다.
_HANDLERS: dict[str, Callable[[dict], Any]] = {}


def register(job_type: str, handler: Callable[[dict], Any]) -> None:
    """잡 타입 핸들러를 등록한다."""
    _HANDLERS[job_type] = handler
    logger.info("워커 핸들러 등록: %s", job_type)


def run_one(lease_seconds: int = 300) -> bool:
    """잡 1개를 집어 처리한다. 처리했으면 True, 큐가 비었으면 False."""
    job = job_queue.claim_next(lease_seconds=lease_seconds)
    if not job:
        return False

    job_id = job["id"]
    job_type = job["job_type"]
    handler = _HANDLERS.get(job_type)
    try:
        if handler is None:
            raise ValueError(f"알 수 없는 job_type: {job_type}")
        result = handler(job.get("payload") or {})
        job_queue.complete(job_id, result)
        logger.info("잡 완료: %s (type=%s)", job_id, job_type)
    except Exception as e:  # noqa: BLE001 — 잡 실패는 격리해 큐를 계속 돌린다
        logger.exception("잡 처리 실패: %s (type=%s)", job_id, job_type)
        job_queue.fail(job_id, str(e), job.get("attempts", 1), job.get("max_attempts", 3))
    return True


def poll_loop(interval: float = 2.0, stop_event: threading.Event | None = None) -> None:
    """큐를 폴링하며 잡을 처리한다. stop_event 가 set 되면 종료."""
    logger.info("워커 poll loop 시작 (interval=%.1fs, handlers=%s)",
                interval, list(_HANDLERS))
    while stop_event is None or not stop_event.is_set():
        try:
            worked = run_one()
        except Exception:  # noqa: BLE001 — 루프는 어떤 예외에도 죽지 않는다
            logger.exception("워커 루프 오류")
            worked = False
        if not worked:
            # 큐가 비었으면 잠시 쉼(빈 폴링 억제)
            if stop_event is not None:
                stop_event.wait(interval)
            else:
                time.sleep(interval)


# ── embedded 모드 (FastAPI startup 에서 백그라운드 스레드) ──────────────────────

_embedded_stop: threading.Event | None = None
_embedded_thread: threading.Thread | None = None


def start_embedded_worker(interval: float = 2.0) -> None:
    """백그라운드 데몬 스레드로 poll_loop 를 띄운다(중복 방지)."""
    global _embedded_stop, _embedded_thread
    if _embedded_thread and _embedded_thread.is_alive():
        return
    _embedded_stop = threading.Event()
    _embedded_thread = threading.Thread(
        target=poll_loop, kwargs={"interval": interval, "stop_event": _embedded_stop},
        name="job-worker", daemon=True,
    )
    _embedded_thread.start()
    logger.info("embedded 워커 스레드 시작")


def stop_embedded_worker() -> None:
    """embedded 워커에 종료 신호를 보낸다(그레이스풀)."""
    if _embedded_stop is not None:
        _embedded_stop.set()
        logger.info("embedded 워커 종료 신호")


if __name__ == "__main__":
    # standalone 폴러: python -m modules.worker
    # 핸들러 등록을 위해 라우터 모듈을 import 한다(등록 부작용).
    import backend.routers.upload  # noqa: F401  (worker.register 호출됨)

    logging.basicConfig(level=logging.INFO)
    poll_loop()
