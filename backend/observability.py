"""
[역할] 관측(Observability) — 구조화 로깅 + 요청 ID (Sprint 4)

지금까지 로깅 설정이 없어 로그가 사실상 버려졌고(핸들러/포맷 미설정), 요청 하나를
가로질러 무슨 일이 있었는지 추적할 수 없었다. 이 모듈은 세 가지를 채운다:
  1. 구조화 로깅   — setup_logging(): 루트 로거에 핸들러·포맷 설정(text 또는 JSON)
  2. 요청 ID       — contextvar + 필터로 모든 로그 레코드에 request_id 주입
  3. 요청 추적     — RequestIdMiddleware(순수 ASGI)가 요청당 id 발급 + 응답 헤더 반영

설계 메모:
  - request_id 는 contextvar 로 흐른다. 미들웨어를 **순수 ASGI**로 둔 이유:
    Starlette BaseHTTPMiddleware 는 별도 컨텍스트에서 돌아 contextvar 가 엔드포인트
    핸들러까지 안 흐르는 함정이 있다. 순수 ASGI 는 같은 태스크 컨텍스트라 안전.
  - 포맷은 LOG_FORMAT=json 이면 JSON(프로덕션 수집용), 아니면 사람이 읽는 text(개발).
"""
from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from contextvars import ContextVar

# 요청 범위 식별자 — 요청 시작 시 미들웨어가 설정, 로그 필터가 읽는다.
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    """모든 로그 레코드에 현재 요청의 request_id 를 붙인다."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """로그 레코드를 한 줄 JSON 으로 직렬화(수집·검색용)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts":         self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level":      record.levelname,
            "logger":     record.name,
            "request_id": getattr(record, "request_id", "-"),
            "msg":        record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging() -> None:
    """루트 로거를 설정한다. LOG_LEVEL(기본 INFO)·LOG_FORMAT(text|json, 기본 text)."""
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    use_json = os.getenv("LOG_FORMAT", "text").lower() == "json"

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())
    if use_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)-7s [%(request_id)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        ))

    root = logging.getLogger()
    root.handlers.clear()      # uvicorn/기본 핸들러 중복 제거
    root.addHandler(handler)
    root.setLevel(level)


class RequestIdMiddleware:
    """순수 ASGI 미들웨어 — 요청당 request_id 발급 후 contextvar 에 심고,
    응답에 X-Request-ID 헤더를 붙인다. 클라가 X-Request-ID 를 보내면 그대로 이어받는다.
    """

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        incoming = headers.get(b"x-request-id", b"").decode() or uuid.uuid4().hex[:12]
        token = request_id_var.set(incoming)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                message.setdefault("headers", [])
                message["headers"].append((b"x-request-id", incoming.encode()))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            request_id_var.reset(token)
