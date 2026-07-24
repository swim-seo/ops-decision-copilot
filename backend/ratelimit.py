"""
[역할] 레이트리밋 — 공개 데모 비용/남용 보호 (Sprint 4 배포)

이 앱은 채팅·업로드마다 Claude API 를 호출한다(=비용). 공개 링크에서 아무나
연타하면 크레딧이 샌다. IP 별 슬라이딩 윈도우로 분당 요청 수를 제한한다.

경량 원칙: 외부 의존성(Redis) 없이 인메모리. 단일 인스턴스 데모에 충분하다.
멀티 인스턴스로 확장하면 공유 저장소(Redis 등)가 필요 — 데모 한계로 명시.
/api/health 와 비-API 경로는 제외한다.
"""
from __future__ import annotations

import logging
import os
import time
from collections import defaultdict, deque

from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

_WINDOW_SECONDS = 60
_MAX_PER_WINDOW = int(os.getenv("RATE_LIMIT_PER_MIN", "30"))
_MAX_TRACKED_IPS = 10_000   # 메모리 폭주 방지(초과 시 오래된 것부터 정리)

_hits: dict[str, deque] = defaultdict(deque)


def _client_ip(scope) -> str:
    """프록시(Railway 등) 뒤에서는 X-Forwarded-For 첫 IP, 아니면 소켓 주소."""
    headers = dict(scope.get("headers") or [])
    xff = headers.get(b"x-forwarded-for", b"").decode()
    if xff:
        return xff.split(",")[0].strip()
    client = scope.get("client")
    return client[0] if client else "unknown"


def _prune_if_needed() -> None:
    """추적 IP 가 너무 많아지면 빈 deque 를 정리한다(간단한 방어)."""
    if len(_hits) <= _MAX_TRACKED_IPS:
        return
    empty = [ip for ip, dq in _hits.items() if not dq]
    for ip in empty:
        _hits.pop(ip, None)


class RateLimitMiddleware:
    """순수 ASGI 미들웨어 — IP 별 분당 요청 수 제한. 초과 시 429."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not path.startswith("/api/") or path == "/api/health":
            await self.app(scope, receive, send)
            return

        ip = _client_ip(scope)
        now = time.monotonic()
        dq = _hits[ip]
        # 윈도우 밖 기록 제거
        while dq and dq[0] <= now - _WINDOW_SECONDS:
            dq.popleft()

        if len(dq) >= _MAX_PER_WINDOW:
            logger.warning("레이트리밋 초과: ip=%s path=%s (%d/min)", ip, path, _MAX_PER_WINDOW)
            resp = JSONResponse(
                {"detail": f"요청이 너무 많습니다. 분당 {_MAX_PER_WINDOW}회로 제한됩니다."},
                status_code=429,
            )
            await resp(scope, receive, send)
            return

        dq.append(now)
        _prune_if_needed()
        await self.app(scope, receive, send)
