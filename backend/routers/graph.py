from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from backend.routers.upload import _get_or_create_kg

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


@router.get("/data")
def get_graph_data(collection_name: str = "domain_docs"):
    kg = _get_or_create_kg(collection_name)
    nodes = [
        {"id": n, **kg.graph.nodes[n]}
        for n in kg.graph.nodes
    ]
    edges = [
        {"source": u, "target": v, **kg.graph.edges[u, v]}
        for u, v in kg.graph.edges
    ]
    return {"nodes": nodes, "edges": edges}
