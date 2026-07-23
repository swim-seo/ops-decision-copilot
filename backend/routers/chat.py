from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from modules import chat_copilot
from modules.rag_engine import RAGEngine
from modules.claude_client import ClaudeClient
from modules.agent import run_agent
from modules.agent_tools import ToolContext
from modules.retrieval_profiles import resolve_department
from backend.routers.upload import _get_or_create_kg

router = APIRouter()


class ChatRequest(BaseModel):
    message:         str
    collection_name: str = "domain_docs"
    domain_context:  str = ""
    stream:          bool = True


class AgentRequest(BaseModel):
    message:         str
    collection_name: str = "domain_docs"
    domain_context:  str = ""
    department:      str = ""   # 부서 렌즈 (Sprint 3 Step 1) — Step 2 에서 JWT 로 대체


@router.post("/message")
def chat_message(req: ChatRequest):
    rag    = RAGEngine(collection_name=req.collection_name)
    kg     = _get_or_create_kg(req.collection_name)
    claude = ClaudeClient()

    if req.stream:
        def generate():
            for chunk in chat_copilot.respond_stream(
                req.message, claude, rag, kg, req.domain_context
            ):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    result = chat_copilot.respond(req.message, claude, rag, kg, req.domain_context)
    return {
        "text":  result.text,
        "route": result.route,
        "charts": [fig.to_json() for fig in (result.charts or [])],
    }


@router.post("/agent")
def chat_agent(req: AgentRequest):
    """LangGraph 에이전트 엔드포인트 (Sprint 1).

    detect_route() 규칙 라우팅 대신 LLM이 툴(search_documents/search_graph/
    analyze_data/get_briefing)을 스스로 골라 plan→act→reflect 루프를 돈다.
    기존 /message 는 그대로 유지 — 이 엔드포인트는 안전한 병행 진입점이다.

    응답의 tools_used 는 "어떤 근거로 답했나"를 보여주는 배지용.
    스트리밍은 추후(agent.invoke 가 현재 블로킹).
    """
    ctx = ToolContext(
        claude=ClaudeClient(),
        rag=RAGEngine(collection_name=req.collection_name),
        kg=_get_or_create_kg(req.collection_name),
        domain_context=req.domain_context,
        collection_name=req.collection_name,
        department=resolve_department(req.department),  # 부서 렌즈 seam (Step 2: JWT)
    )
    result = run_agent(req.message, ctx)
    return {
        "text":       result["text"],
        "tools_used": result["tools_used"],
        "iterations": result["iterations"],
    }
