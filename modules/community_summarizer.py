"""
[역할] GraphRAG 커뮤니티 요약 생성·저장·검색

GraphRAG의 핵심 로직을 담당합니다.
  - build_community_summaries() : KG 커뮤니티 탐지 → Claude로 요약 → Supabase 저장
                                  문서 업로드 시 1회 실행 (KG 구축 완료 후)
  - retrieve_community_context(): 질문 임베딩 → 유사 커뮤니티 요약 검색 → 컨텍스트 반환
                                  채팅 응답 시마다 호출

일반 RAG와의 차이:
  - RAG        : 질문 ↔ 문서 청크 유사도 검색 (문장 수준)
  - GraphRAG   : 질문 ↔ 커뮤니티 요약 유사도 검색 (개념 묶음 수준)
               + 멀티홉 그래프 탐색 (A→B→C 관계 체인 추적)
"""
import json
import logging
import uuid
from typing import Optional

import requests
from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL
import modules.supabase_client as _sb

logger = logging.getLogger(__name__)

_TABLE = "community_summaries"
_model: Optional[SentenceTransformer] = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


# ── 커뮤니티 요약 빌드 (문서 업로드 시 호출) ──────────────────────────────────

def build_community_summaries(kg, claude, collection_name: str) -> int:
    """KG 커뮤니티를 탐지하고 각 커뮤니티 요약을 Claude로 생성해 Supabase에 저장합니다.

    흐름:
      KG.detect_communities()  → [(node1, node2, ...), ...]
      각 커뮤니티 → 노드/엣지 텍스트화 → Claude 요약
      요약 임베딩 생성 → Supabase community_summaries 테이블에 저장
    """
    if not _sb.is_connected():
        logger.warning("Supabase 미연결 — 커뮤니티 요약 저장 건너뜀")
        return 0

    communities = kg.detect_communities()
    if not communities:
        logger.info("GraphRAG: 커뮤니티 없음 (노드 수 부족)")
        return 0

    # 기존 요약 삭제 (재업로드 시 갱신)
    _sb.delete_rows(_TABLE, {"collection_name": f"eq.{collection_name}"})

    model = _get_model()
    records = []

    for cid, node_list in enumerate(communities):
        subgraph_text = _community_to_text(kg, node_list)

        prompt = (
            "다음은 지식 그래프에서 서로 밀접하게 연결된 개념 묶음(커뮤니티)입니다.\n\n"
            f"{subgraph_text}\n\n"
            "이 커뮤니티에서 다루는 핵심 개념과 관계를 3~5문장으로 요약하세요. "
            "어떤 개체들이 어떻게 연결되어 있으며 어떤 의사결정에 활용될 수 있는지 포함하세요."
        )
        try:
            summary = claude.generate(prompt, max_tokens=300)
        except Exception as e:
            logger.warning("커뮤니티 %d 요약 생성 실패: %s", cid, e)
            continue

        embedding = model.encode(summary, normalize_embeddings=True).tolist()
        records.append({
            "id":              f"{collection_name}_c{cid}_{uuid.uuid4().hex[:6]}",
            "collection_name": collection_name,
            "community_id":    cid,
            "node_list":       json.dumps(node_list, ensure_ascii=False),
            "summary":         summary,
            "embedding":       embedding,
        })

    if not records:
        return 0

    headers = {**_sb._headers(), "Prefer": "resolution=merge-duplicates"}
    r = requests.post(
        f"{_sb._url}/rest/v1/{_TABLE}",
        headers=headers,
        data=json.dumps(records, ensure_ascii=False),
        timeout=30,
    )
    if r.status_code not in (200, 201, 204):
        logger.error("커뮤니티 요약 저장 실패 (HTTP %s): %s", r.status_code, r.text)
        return 0

    logger.info("GraphRAG: %d개 커뮤니티 요약 저장 완료 (컬렉션: %s)", len(records), collection_name)
    return len(records)


# ── 커뮤니티 요약 검색 (채팅 응답 시 호출) ────────────────────────────────────

def retrieve_community_context(question: str, collection_name: str, top_k: int = 3) -> str:
    """질문과 의미적으로 유사한 커뮤니티 요약을 검색해 컨텍스트 문자열로 반환합니다.

    일반 RAG와 달리 '문서 청크'가 아닌 '개념 묶음 요약'을 검색합니다.
    → 특정 단어가 없어도 관련 개념 그룹을 찾을 수 있습니다.
    """
    if not _sb.is_connected():
        return ""

    model = _get_model()
    embedding = model.encode(question, normalize_embeddings=True).tolist()

    rows = _sb.rpc("match_community_summaries", {
        "query_embedding": embedding,
        "collection":      collection_name,
        "match_count":     top_k,
    })

    if not rows:
        return ""

    parts = []
    for row in rows:
        try:
            nodes = json.loads(row.get("node_list", "[]"))
        except (json.JSONDecodeError, TypeError):
            nodes = []
        nodes_preview = ", ".join(nodes[:8])
        similarity = round(float(row.get("similarity", 0)), 3)
        parts.append(
            f"[그래프 커뮤니티 (유사도 {similarity}) — 관련 개념: {nodes_preview}]\n"
            f"{row['summary']}"
        )

    return "\n\n".join(parts)


# ── 내부 헬퍼 ─────────────────────────────────────────────────────────────────

def _community_to_text(kg, node_list: list) -> str:
    """커뮤니티 내 노드·엣지를 Claude 프롬프트용 텍스트로 변환합니다."""
    lines = ["[노드]"]
    for node in node_list[:15]:
        attrs = kg.graph.nodes.get(node, {})
        label = attrs.get("label", node)
        node_type = attrs.get("type", "")
        lines.append(f"  - {label} (유형: {node_type})")

    lines.append("[관계]")
    edge_count = 0
    for src, tgt, data in kg.graph.edges(data=True):
        if src in node_list and tgt in node_list and edge_count < 20:
            rel = data.get("relation", "관련")
            lines.append(f"  - {src} → {rel} → {tgt}")
            edge_count += 1

    return "\n".join(lines)
