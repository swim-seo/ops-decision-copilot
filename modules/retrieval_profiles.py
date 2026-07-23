"""
[역할] 부서별 가중치 RAG — retrieval_profiles 로드 + 검색 시점 재랭킹 (Sprint 3, Step 1)

"같은 지식그래프, 부서별 렌즈." 하나의 공유 그래프에 부서마다 검색 가중치를 두고,
검색 '시점'에 커뮤니티 후보를 재정렬한다(사전계산 X — Codex Q3: 프로파일이 자주 바뀜).

설계(Codex 리뷰):
  - Q1 타입 있는 신호만 가중: 커뮤니티/KG(노드 type 보유)에만 부스트. 문서 청크는 미가중.
  - Q2 Python 재랭킹: RPC 로 후보를 넓게 받아 앱 계층에서 가중·정렬(유연·저위험).
  - Q4 resolve_department seam: 지금은 요청 파라미터, Step 2 에서 JWT 클레임으로 교체.
  - 정규화: 커뮤니티 유사도를 후보 내 max 로 나눠 [0,1] 스케일 맞춘 뒤 가중(랭킹 왜곡 방지).

레이어링: 이 모듈은 프로파일·가중 로직만 담당. 커뮤니티 조회/포맷은 community_summarizer,
조합(툴 배선)은 agent_tools 가 맡는다(단일 책임).
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

import modules.supabase_client as _sb

logger = logging.getLogger(__name__)

_TABLE = "retrieval_profiles"

# 부서 미지정/프로파일 없음 → 이 기본값(가중 없음 = 기존 동작과 동일)
_DEFAULT_COMMUNITY_WEIGHT = 1.0


@dataclass(frozen=True)
class RetrievalProfile:
    """부서 검색 프로파일 (불변)."""
    community_weight: float = _DEFAULT_COMMUNITY_WEIGHT
    node_type_boost:  dict[str, float] = field(default_factory=dict)

    @property
    def is_default(self) -> bool:
        return self.community_weight == _DEFAULT_COMMUNITY_WEIGHT and not self.node_type_boost


DEFAULT_PROFILE = RetrievalProfile()


def resolve_department(department: str | None) -> str:
    """요청에서 넘어온 부서명을 정규화한다 [seam].

    지금(Step 1): 요청 파라미터를 sanitize 해서 사용한다.
    다음(Step 2): 같은 함수가 JWT 의 `department` 클레임에서 값을 읽도록 교체 →
                 위조 가능한 파라미터 경로를 제거(호출부는 그대로 유지).

    별도 하드코딩 allowlist 를 두지 않는 이유: 유효 부서의 실질 게이트는
    '프로파일 존재 여부'다(없으면 DEFAULT_PROFILE → 무가중). 여기선 남용 방지를 위한
    sanitize + 사용 로깅만 한다. 신뢰 경계는 Step 2 인증에서 세운다.
    """
    if not department:
        return ""
    cleaned = re.sub(r"\s+", "", str(department))[:40]
    logger.info("retrieval: 부서 렌즈 요청 department=%r", cleaned)
    return cleaned


def get_profile(org_id: str, department: str) -> RetrievalProfile:
    """(org_id, department) 프로파일을 로드한다. 없거나 미연결이면 DEFAULT_PROFILE.

    org_id 는 Step 1 임시로 collection_name 을 사용한다(Step 2: JWT org_id).
    """
    if not department:
        return DEFAULT_PROFILE

    row = _sb.select_one(_TABLE, {
        "org_id":     f"eq.{org_id}",
        "department": f"eq.{department}",
    })
    if not row:
        logger.info("retrieval: 프로파일 없음 (org=%s, dept=%s) — 기본 무가중", org_id, department)
        return DEFAULT_PROFILE

    return RetrievalProfile(
        community_weight=float(row.get("community_weight", _DEFAULT_COMMUNITY_WEIGHT)),
        node_type_boost=_coerce_boost(row.get("node_type_boost")),
    )


def rerank_communities(
    candidates: list[dict], kg: Any, profile: RetrievalProfile, top_k: int
) -> list[dict]:
    """커뮤니티 후보를 부서 프로파일로 재랭킹해 상위 top_k 를 반환한다.

    final = norm_similarity × community_weight × mean(node_type_boost[node.type])
      - norm_similarity: 후보 내 최대 유사도로 나눈 [0,1] 값(소스 내 스케일 정규화).
      - node_type_boost: 커뮤니티 소속 노드들의 타입 부스트 평균(타입은 kg 에서 조회).
    프로파일이 기본값이면 원래 순서(유사도순)를 그대로 유지한다.
    """
    if not candidates:
        return []
    if profile.is_default or kg is None:
        return candidates[:top_k]

    sims = [float(c.get("similarity", 0.0)) for c in candidates]
    hi = max(sims) or 1.0

    scored: list[tuple[float, dict]] = []
    for c in candidates:
        norm_sim = float(c.get("similarity", 0.0)) / hi
        boost = _community_type_boost(kg, c.get("node_list"), profile.node_type_boost)
        final = norm_sim * profile.community_weight * boost
        scored.append((final, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]


# ── 내부 헬퍼 ─────────────────────────────────────────────────────────────────

def _coerce_boost(raw: Any) -> dict[str, float]:
    """node_type_boost 를 {type: float} dict 로 정규화 (JSONB dict 또는 JSON 문자열)."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for k, v in raw.items():
        try:
            out[str(k)] = float(v)
        except (TypeError, ValueError):
            continue
    return out


def _community_type_boost(kg: Any, node_list: Any, boost_map: dict[str, float]) -> float:
    """커뮤니티 노드들의 타입 부스트 평균. 타입 매칭 없으면 1.0(중립)."""
    if not boost_map:
        return 1.0
    if isinstance(node_list, str):
        try:
            node_list = json.loads(node_list)
        except (json.JSONDecodeError, TypeError):
            node_list = []
    if not node_list:
        return 1.0

    vals = []
    for node_id in node_list:
        node_type = kg.graph.nodes.get(node_id, {}).get("type", "")
        vals.append(boost_map.get(node_type, 1.0))
    return sum(vals) / len(vals) if vals else 1.0
