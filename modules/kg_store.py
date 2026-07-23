"""
[역할] 지식그래프 저장소 — Sprint 1, Step 3 (데모 부트스트랩 스톱갭)

문제: KG는 프로세스 메모리(`upload.py`의 dict)에만 있어 서버 재시작 시 소실된다.
반면 RAG(Supabase pgvector)는 영속이라, 재시작 후 LangGraph 에이전트의
`search_graph` 툴만 빈 그래프를 조회해 조용히 "자료 없음"을 반환한다(반쪽 고장).

해결(임시): 어떤 collection이 처음 요청될 때 그래프가 비어 있으면,
디스크의 데모 데이터셋(`data/<sample>/`)에서 KG를 **결정적으로** 재구축한다.
결정적 경로만 사용 — CSV 스키마 + SCHEMA_DEFINITION.json. Claude(LLM) 호출 없음
(비용·비결정성 회피, Codex 리뷰 반영). LOGIC_DOCUMENT.txt 등 LLM 추출 경로는 건너뜀.

Sprint 2 예고: InMemoryKnowledgeGraphStore → Supabase 백엔드(도메인별 JSON blob)로
교체한다. KnowledgeGraphStore 인터페이스가 그 교체 지점(seam)이다. 호출부는
`get()`/`save()`만 알면 되므로 구현체 교체가 drop-in이 되도록 설계했다.

주의: in-memory dict를 "source of truth"로 취급하는 코드를 여기 밖에서 쓰지 말 것
(Sprint 2 교체를 막는 가장 큰 요인 — Codex 지적).
"""
from __future__ import annotations

import json
import logging
import os
import threading
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

from networkx.readwrite import json_graph

import modules.supabase_client as _sb
from modules.document_parser import extract_csv_schema
from modules.knowledge_graph import KnowledgeGraph

logger = logging.getLogger(__name__)

# Supabase 영속 테이블 (scripts/kg_persistence_migration.sql)
_KG_TABLE = "knowledge_graphs"

# 데모 데이터셋 루트 (upload.py의 DATA_DIR과 동일 위치)
_DATA_DIR = Path(__file__).parent.parent / "data"

# collection_name → 데모 샘플 디렉터리명(data/ 하위) 매핑.
# collection 이름이 곧 샘플 id가 아닐 수 있어(예: "domain_sample") 별도 매핑을 둔다.
# 필요 시 OPS_DEMO_SAMPLE 로 기본 데모 샘플을 바꾼다.
_DEMO_COLLECTION = os.getenv("OPS_DEMO_COLLECTION", "domain_sample")
_DEMO_SAMPLE = os.getenv("OPS_DEMO_SAMPLE", "beauty")


def _bootstrap_enabled() -> bool:
    """데모 부트스트랩 활성화 여부. 기본 비활성(프로덕션 오염 방지 — Codex 리스크).

    실제 운영 환경에 데모 데이터가 자동 적재되지 않도록 명시적 opt-in만 허용한다.
    """
    return os.getenv("OPS_DEMO_BOOTSTRAP", "").lower() in ("1", "true", "yes")


def _resolve_sample_dir(collection: str) -> Path | None:
    """collection_name → 재구축에 쓸 데모 샘플 디렉터리 경로.

    우선순위:
      1) collection 이름 자체가 샘플 디렉터리면 그걸 사용 (예: "beauty").
      2) 지정된 데모 collection 이면 기본 데모 샘플(_DEMO_SAMPLE) 사용.
    매칭 없으면 None (부트스트랩 안 함).
    """
    direct = _DATA_DIR / collection
    if direct.is_dir():
        return direct
    if collection == _DEMO_COLLECTION:
        candidate = _DATA_DIR / _DEMO_SAMPLE
        if candidate.is_dir():
            return candidate
    return None


def _rebuild_kg_from_dir(sample_dir: Path) -> KnowledgeGraph:
    """디스크의 데모 디렉터리에서 KG를 결정적으로 재구축 (LLM 호출 없음).

    upload._process_file 의 결정적 부분만 재현한다:
      - SCHEMA_DEFINITION.json  → build_from_schema_json
      - *.csv                   → extract_csv_schema → build_from_csv_schema
    RAG 적재(add_document)는 하지 않는다 — KG 구축과 RAG 인제스트는 분리(Codex 원칙).
    """
    kg = KnowledgeGraph()

    schema_json = sample_dir / "SCHEMA_DEFINITION.json"
    if schema_json.exists():
        data = json.loads(schema_json.read_text(encoding="utf-8"))
        kg.build_from_schema_json(data)

    # CSV: 2-pass FK 해석 — 모든 스키마를 먼저 파싱해 테이블명을 모은 뒤 넘긴다.
    # (upload.py 는 all_table_names 를 안 넘겨 CSV-only 도메인은 FK 엣지가 비지만,
    #  부트스트랩은 전체 목록을 알고 있으므로 관계선까지 복원한다.)
    csv_schemas = [
        extract_csv_schema(p.name, p.read_text(encoding="utf-8", errors="ignore"))
        for p in sorted(sample_dir.glob("*.csv"))
    ]
    all_names = [s.get("table_name", "") for s in csv_schemas if s.get("table_name")]
    for schema in csv_schemas:
        kg.build_from_csv_schema(schema, all_table_names=all_names)

    return kg


# ── KG 직렬화 (networkx ↔ JSON) ────────────────────────────────────────────────

def _serialize_kg(kg: KnowledgeGraph) -> dict:
    """KnowledgeGraph → JSON 직렬화 가능한 dict (networkx node_link_data).

    노드 속성(label/type/title/columns/col_types/fk_cols)·엣지 속성(relation)·
    방향성(DiGraph)이 모두 보존된다(왕복 검증 완료).
    """
    return json_graph.node_link_data(kg.graph, edges="edges")


def _deserialize_kg(data: dict) -> KnowledgeGraph:
    """node_link_data dict → KnowledgeGraph 복원 (directed 유지)."""
    kg = KnowledgeGraph()
    kg.graph = json_graph.node_link_graph(
        data, directed=True, multigraph=False, edges="edges"
    )
    return kg


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class KnowledgeGraphStore(ABC):
    """KG 저장소 인터페이스. Sprint 2에서 Supabase 구현체로 교체될 지점."""

    @abstractmethod
    def get(self, collection: str) -> KnowledgeGraph:
        """collection의 KG를 반환. 없으면 (부트스트랩 가능 시) 재구축, 아니면 빈 그래프."""
        ...

    @abstractmethod
    def save(self, collection: str, kg: KnowledgeGraph) -> None:
        """업로드 등으로 갱신된 KG를 저장소에 반영."""
        ...


class InMemoryKnowledgeGraphStore(KnowledgeGraphStore):
    """프로세스 메모리 기반 구현. 재시작 시 소실되지만, get() 최초 호출에서
    데모 데이터로 결정적 재구축해 '반쪽 고장'을 막는다(스톱갭).

    동시성: 호출부가 동기(chat.py)·비동기(upload.py) 혼재라 asyncio.Lock 대신
    threading.Lock 사용. double-checked locking 으로 재구축 중복을 막는다.
    """

    def __init__(self) -> None:
        self._graphs: dict[str, KnowledgeGraph] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._bootstrapped: set[str] = set()  # 재구축 재시도 1회 제한 (실패해도 무한 반복 방지)
        self._registry_lock = threading.Lock()  # _locks 딕셔너리 자체 보호

    def _lock_for(self, collection: str) -> threading.Lock:
        with self._registry_lock:
            lock = self._locks.get(collection)
            if lock is None:
                lock = threading.Lock()
                self._locks[collection] = lock
            return lock

    def get(self, collection: str) -> KnowledgeGraph:
        # fast path — 이미 있으면 락 없이 반환
        kg = self._graphs.get(collection)
        if kg is not None:
            return kg

        lock = self._lock_for(collection)
        with lock:
            # double-check — 락 대기 중 다른 스레드가 채웠을 수 있음
            kg = self._graphs.get(collection)
            if kg is not None:
                return kg
            kg = self._maybe_bootstrap(collection) or KnowledgeGraph()
            self._graphs[collection] = kg
            return kg

    def save(self, collection: str, kg: KnowledgeGraph) -> None:
        self._graphs[collection] = kg

    def _maybe_bootstrap(self, collection: str) -> KnowledgeGraph | None:
        """데모 데이터에서 KG 재구축 시도. 비활성/매칭없음/실패면 None (→ 빈 그래프)."""
        if collection in self._bootstrapped:
            return None
        self._bootstrapped.add(collection)

        if not _bootstrap_enabled():
            return None

        sample_dir = _resolve_sample_dir(collection)
        if sample_dir is None:
            logger.info("KG bootstrap: '%s'에 매칭되는 데모 샘플 없음 — 스킵", collection)
            return None

        try:
            kg = _rebuild_kg_from_dir(sample_dir)
            logger.info(
                "KG bootstrap: '%s' 재구축 완료 (source=%s, nodes=%d)",
                collection, sample_dir.name, kg.graph.number_of_nodes(),
            )
            return kg
        except Exception:
            logger.exception("KG bootstrap 실패: '%s' (source=%s)", collection, sample_dir)
            return None


class SupabaseKnowledgeGraphStore(KnowledgeGraphStore):
    """Supabase(JSONB blob) 백엔드 KG 저장소 — **read-through(캐시 없음)**.

    캐시를 두지 않는 이유(Codex Q1): 멀티워커 환경에서 프로세스별 캐시는
    Sprint 2가 없애려는 바로 그 '교차 워커 불일치'를 다시 만든다(워커 A가
    업로드해도 워커 B는 낡은 캐시 그래프를 응답). 그래프가 작고(demo 8노드)
    QPS 낮은 현 단계에선 매 요청 DB 1회 + 역직렬화가 정답이다.
    전환 기준: p95 지연/비용이 문제되거나 노드 수천 개↑ →
              updated_at 버전체크 + 짧은 TTL(수 초) 캐시 도입.
    """

    def get(self, collection: str) -> KnowledgeGraph:
        row = _sb.select_one(_KG_TABLE, {"collection_name": f"eq.{collection}"})
        if row and row.get("graph_json"):
            try:
                return _deserialize_kg(row["graph_json"])
            except Exception:
                logger.exception("KG 역직렬화 실패: '%s' — 빈 그래프로 폴백", collection)
                return KnowledgeGraph()

        # 행 없음 → 데모 부트스트랩(활성 시)하고 **DB에 저장**한다.
        # save-back 은 필수(Codex): 안 하면 워커마다 독립적으로 재시딩해 발산.
        # 결정적 재구축이라 동시 double-save 도 동일 blob → 수렴(멱등).
        kg = self._maybe_bootstrap(collection)
        if kg is not None and kg.graph.number_of_nodes() > 0:
            self.save(collection, kg)
            return kg
        return KnowledgeGraph()

    def save(self, collection: str, kg: KnowledgeGraph) -> None:
        record = {
            "collection_name": collection,
            "graph_json":      _serialize_kg(kg),
            "node_count":      kg.graph.number_of_nodes(),
            "edge_count":      kg.graph.number_of_edges(),
            "updated_at":      _now_iso(),
        }
        if not _sb.upsert_rows(_KG_TABLE, [record]):
            logger.error("KG 저장 실패: '%s'", collection)

    def _maybe_bootstrap(self, collection: str) -> KnowledgeGraph | None:
        """데모 데이터에서 KG 재구축 시도. 비활성/매칭없음/실패면 None.

        (InMemory 와 달리 재시도 1회 제한 불필요 — 성공 시 save-back 으로 다음
         get() 은 행을 찾고, 매칭 실패는 _resolve_sample_dir 가 즉시 None 반환해 저렴.)
        """
        if not _bootstrap_enabled():
            return None
        sample_dir = _resolve_sample_dir(collection)
        if sample_dir is None:
            logger.info("KG bootstrap: '%s'에 매칭되는 데모 샘플 없음 — 스킵", collection)
            return None
        try:
            kg = _rebuild_kg_from_dir(sample_dir)
            logger.info(
                "KG bootstrap(supabase): '%s' 재구축 (source=%s, nodes=%d) — DB 저장",
                collection, sample_dir.name, kg.graph.number_of_nodes(),
            )
            return kg
        except Exception:
            logger.exception("KG bootstrap 실패: '%s' (source=%s)", collection, sample_dir)
            return None


def get_kg_store() -> KnowledgeGraphStore:
    """환경변수 `KG_STORE` 로 저장소 구현을 명시적으로 선택한다(Codex Q2).

    - `KG_STORE=supabase` → SupabaseKnowledgeGraphStore (영속·멀티워커 안전)
    - 그 외/미설정        → InMemoryKnowledgeGraphStore (개발 기본·재시작 소실)

    auto-detect(is_connected) 대신 명시적 플래그를 쓰는 이유: 연결이 불안정할 때
    동작이 예측 가능하고 demo/prod 분리가 흐려지지 않는다.
    """
    if os.getenv("KG_STORE", "").lower() == "supabase":
        logger.info("KG store: Supabase (영속)")
        return SupabaseKnowledgeGraphStore()
    logger.info("KG store: in-memory (개발 기본)")
    return InMemoryKnowledgeGraphStore()
