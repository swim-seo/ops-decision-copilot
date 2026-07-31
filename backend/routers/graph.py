from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from backend.routers.upload import _get_or_create_kg
from modules.knowledge_graph import TABLE_NODE_TYPES

router = APIRouter()


@router.get("/html", response_class=HTMLResponse)
def get_graph_html(collection_name: str = "domain_docs"):
    kg = _get_or_create_kg(collection_name)
    if len(kg.graph.nodes) == 0:
        return HTMLResponse("<p style='font-family:sans-serif;padding:2rem;color:#94a3b8'>업로드된 파일이 없습니다.</p>")
    result = kg.render_html()
    # render_html()은 파일 경로 또는 HTML 문자열을 반환
    if result and not result.startswith("<"):
        path = Path(result)
        if path.exists():
            return HTMLResponse(path.read_text(encoding="utf-8"))
        return HTMLResponse("<p style='font-family:sans-serif;padding:2rem;color:#ef4444'>그래프 파일을 찾을 수 없습니다.</p>")
    return HTMLResponse(result or "")


def _fk_edge_payload(kg, u: str, v: str) -> dict:
    """엣지 하나를 직렬화한다. 스키마 FK 엣지면 조인 키를 1급 필드로 노출한다.

    join_key 는 최근에 추가된 속성이라, 그 전에 저장돼 이미 Supabase 에 들어 있는
    그래프에는 없다. 그런 엣지는 relation 에 조인 키가 들어 있으므로 거기서 끌어와
    재적재 없이도 응답 형태를 맞춘다. 문서 엔티티 KG 의 엣지는 relation 이 "관련"
    같은 서술어라 조인 키가 아니므로, 양끝이 모두 테이블 노드일 때만 채운다.
    """
    data = dict(kg.graph.edges[u, v])
    payload = {"source": u, "target": v, **data}

    both_tables = all(
        kg.graph.nodes[n].get("type") in TABLE_NODE_TYPES for n in (u, v)
    )
    if not both_tables:
        return payload

    keys = data.get("join_keys")
    if not keys:
        legacy = data.get("join_key") or data.get("relation") or ""
        keys = [k.strip() for k in legacy.split(",") if k.strip()]

    payload["join_keys"] = keys
    payload["join_key"] = keys[0] if keys else ""
    return payload


@router.get("/data")
def get_graph_data(collection_name: str = "domain_docs"):
    kg = _get_or_create_kg(collection_name)
    nodes = [
        {"id": n, **kg.graph.nodes[n]}
        for n in kg.graph.nodes
    ]
    edges = [_fk_edge_payload(kg, u, v) for u, v in kg.graph.edges]
    return {"nodes": nodes, "edges": edges}
