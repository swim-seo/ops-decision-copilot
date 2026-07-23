"""
[역할] 인증 — Supabase Auth 토큰 검증 (Sprint 3 Step 2, 데모용 경량)

지금까지 collection_name/department 를 클라이언트가 파라미터로 보내 위조 가능했다.
이 모듈은 요청의 Bearer 토큰을 검증해 신원(user_id/org_id/department)을 서버가
도출하는 층을 얹는다. resolve_department seam(Step 1)의 실제 소스가 여기로 이동한다.

설계(Codex 리뷰):
  - 검증 방식: Supabase `GET /auth/v1/user` 에 토큰을 되물어 유효성 확인.
    JWT 시크릿/JWKS 를 직접 다루지 않아 데모 최단경로이자, Supabase 의 비대칭키
    (JWKS) 전환에도 영향받지 않는 미래호환 선택.
  - 선택적 인증(honor-if-present): 유효 토큰이 있으면 그 클레임으로 신원 도출,
    없으면 익명 컨텍스트 반환(호출부가 요청 파라미터로 폴백 = 데모 모드).
    AUTH_REQUIRED=true 면 토큰 없는 요청을 401 로 거부(프로덕션).
  - 신뢰 경계: org_id/department 는 app_metadata(관리자 설정=신뢰)에서만 곧바로
    신뢰한다. user_metadata(사용자 편집 가능=비신뢰)는 서버 allow-list 로 검증한
    뒤에만 사용한다(데모에서 admin API 없이 신뢰 경계를 시연).
  - ⚠️ 백엔드는 service key 로 Supabase 에 접근 → RLS 를 우회한다. 따라서 조직
    격리는 서버 코드가 클레임 기반으로 직접 강제해야 한다. service key 는 서버
    전용이며 절대 클라이언트에 노출하지 않는다.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import requests
from fastapi import Header, HTTPException

from config import AUTH_REQUIRED, SUPABASE_KEY, SUPABASE_URL

logger = logging.getLogger(__name__)

# 데모 allow-list — user_metadata(비신뢰)에서 온 값은 이 목록에 있을 때만 수용한다.
# 프로덕션에선 조직/부서 매핑 테이블이나 app_metadata(신뢰)로 대체한다.
_ALLOWED_ORGS = {"domain_sample"}
_ALLOWED_DEPARTMENTS = {"영업부", "재고부"}


@dataclass(frozen=True)
class UserContext:
    """요청의 인증 신원. 미인증이면 is_authenticated=False, 나머지는 빈 값."""
    user_id:          str = ""
    email:            str = ""
    org_id:           str = ""
    department:       str = ""
    is_authenticated: bool = False

    @classmethod
    def anonymous(cls) -> "UserContext":
        return cls()


def verify_token(token: str) -> Optional[dict]:
    """Bearer 토큰을 Supabase 에 되물어 검증한다. 유효하면 user JSON, 아니면 None.

    /auth/v1/user 는 apikey(프로젝트 키) + Authorization(사용자 토큰)을 요구한다.
    네트워크/검증 실패는 모두 None 으로 흡수(요청을 인증 실패로 처리).
    """
    if not token or not SUPABASE_URL:
        return None
    try:
        r = requests.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={"Authorization": f"Bearer {token}", "apikey": SUPABASE_KEY},
            timeout=8,
        )
        if r.status_code == 200:
            return r.json()
        logger.info("토큰 검증 실패 (HTTP %s)", r.status_code)
        return None
    except Exception as e:  # noqa: BLE001 — 검증 실패는 인증 거부로 흡수
        logger.warning("토큰 검증 중 오류: %s", e)
        return None


def get_current_user(authorization: Optional[str] = Header(default=None)) -> UserContext:
    """FastAPI 의존성 — 요청의 Bearer 토큰으로 UserContext 를 만든다.

    유효 토큰 → 클레임 기반 신원. 토큰 없음/무효 → AUTH_REQUIRED 면 401,
    아니면 익명(호출부가 데모 파라미터로 폴백).
    """
    token = _extract_bearer(authorization)
    user_json = verify_token(token) if token else None

    if user_json:
        return _context_from_user(user_json)

    if AUTH_REQUIRED:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    return UserContext.anonymous()


# ── 내부 헬퍼 ─────────────────────────────────────────────────────────────────

def _extract_bearer(authorization: Optional[str]) -> str:
    """'Bearer <token>' 헤더에서 토큰만 추출. 형식 안 맞으면 빈 문자열."""
    if not authorization:
        return ""
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return ""


def _context_from_user(user_json: dict) -> UserContext:
    """Supabase user JSON → UserContext. app_metadata 우선(신뢰), user_metadata 는 검증 후."""
    app_meta = user_json.get("app_metadata") or {}
    user_meta = user_json.get("user_metadata") or {}

    org_id = app_meta.get("org_id") or _validated(user_meta.get("org_hint"), _ALLOWED_ORGS)
    department = (
        app_meta.get("department")
        or _validated(user_meta.get("department"), _ALLOWED_DEPARTMENTS)
    )

    return UserContext(
        user_id=user_json.get("id", ""),
        email=user_json.get("email", ""),
        org_id=org_id or "",
        department=department or "",
        is_authenticated=True,
    )


def _validated(value: Optional[str], allow: set[str]) -> str:
    """비신뢰 값은 allow-list 에 있을 때만 통과(신뢰 경계). 아니면 빈 문자열."""
    return value if value in allow else ""
