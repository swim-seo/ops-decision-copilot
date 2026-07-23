"""
[역할] FastMCP 서버 — AI 오케스트레이션 층 (Sprint 1, Step 4)

agent_tools.py 의 4개 툴을 MCP(Model Context Protocol)로 노출한다.
같은 코어(run_tool)를 두 진입점이 공유한다:
  - HTTP  : backend/routers/chat.py  POST /agent  (LangGraph 에이전트가 툴 사용)
  - MCP   : 이 파일                   Cursor·Claude Desktop 이 툴을 직접 호출

실행:
    .venv/Scripts/python mcp_server.py            # stdio (Claude Desktop/Cursor 연결용)
    .venv/Scripts/python mcp_server.py --http     # streamable-http (127.0.0.1:8001)

주의:
  - 이 프로세스는 uvicorn 과 별도라 in-memory KG 를 공유하지 않는다. 데모에선
    OPS_DEMO_BOOTSTRAP=1 로 데모 그래프를 결정적으로 재구축해 쓴다(kg_store).
  - modules/ 프레임워크 독립 원칙 유지 — 이 파일은 backend/ 를 import 하지 않고
    kg_store 를 직접 소유한다(별도 프로세스이므로 어차피 상태 공유 불가).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from fastmcp import FastMCP

from modules.agent_tools import ToolContext, run_tool
from modules.claude_client import ClaudeClient
from modules.kg_store import InMemoryKnowledgeGraphStore
from modules.rag_engine import RAGEngine

mcp = FastMCP("Ops Decision Copilot")

# HTTP 서버(uvicorn)와 별도 프로세스 → 자체 KG 저장소 소유.
_kg_store = InMemoryKnowledgeGraphStore()


def _context(collection_name: str, domain_context: str = "") -> ToolContext:
    """MCP 툴 호출마다 요청 범위 의존성을 새로 조립한다.

    ClaudeClient/RAGEngine 은 상태가 가벼워 호출당 생성해도 무방하다.
    KG 만 프로세스 수명 동안 재사용(부트스트랩 재구축 비용 회피).
    """
    return ToolContext(
        claude=ClaudeClient(),
        rag=RAGEngine(collection_name=collection_name),
        kg=_kg_store.get(collection_name),
        domain_context=domain_context,
        collection_name=collection_name,
    )


# ── MCP 툴 (agent_tools.run_tool 로 위임 → 에러 격리·로직 단일화) ────────────────

@mcp.tool
def search_documents(
    query: str, collection_name: str = "domain_docs", n_results: int = 4
) -> str:
    """업로드된 문서(회의록·보고서·정책 등)에서 근거 문장을 검색합니다.

    특정 사실·정의·서술형 내용을 문서에서 인용해야 할 때 사용하세요.
    """
    ctx = _context(collection_name)
    return run_tool(ctx, "search_documents", {"query": query, "n_results": n_results})


@mcp.tool
def search_graph(query: str, collection_name: str = "domain_docs") -> str:
    """지식그래프에서 개체 간 관계(원인·영향·연결)를 탐색합니다.

    커뮤니티 요약 검색 + 2-hop 관계 체인을 함께 조회합니다.
    """
    ctx = _context(collection_name)
    return run_tool(ctx, "search_graph", {"query": query})


@mcp.tool
def analyze_data(
    question: str, collection_name: str = "domain_docs", domain_context: str = ""
) -> str:
    """CSV/테이블 기반 정량 분석(수치·랭킹·재고·발주·판매추이)을 수행합니다.

    차트가 필요한 질문도 포함합니다(차트는 개수만 텍스트로 표기).
    """
    ctx = _context(collection_name, domain_context)
    return run_tool(ctx, "analyze_data", {"question": question})


@mcp.tool
def get_briefing(
    collection_name: str = "domain_docs", domain_context: str = ""
) -> str:
    """업로드 자료 전반의 요약·리스크·인사이트·추천 액션을 한 번에 브리핑합니다."""
    ctx = _context(collection_name, domain_context)
    return run_tool(ctx, "get_briefing", {})


if __name__ == "__main__":
    if "--http" in sys.argv:
        mcp.run(transport="http", host="127.0.0.1", port=8001)
    else:
        mcp.run()  # 기본 stdio — Claude Desktop/Cursor 가 프로세스를 spawn
