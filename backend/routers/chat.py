from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from modules import chat_copilot
from modules.rag_engine import RAGEngine
from modules.claude_client import ClaudeClient
from modules.agent import run_agent
from modules.agent_tools import ToolContext
from modules.retrieval_profiles import resolve_department
from backend.auth import UserContext, get_current_user
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
def chat_agent(req: AgentRequest, user: UserContext = Depends(get_current_user)):
    """LangGraph 에이전트 엔드포인트 (Sprint 1 + Sprint 3 인증).

    detect_route() 규칙 라우팅 대신 LLM이 툴(search_documents/search_graph/
    analyze_data/get_briefing)을 스스로 골라 plan→act→reflect 루프를 돈다.
    기존 /message 는 그대로 유지 — 이 엔드포인트는 안전한 병행 진입점이다.

    신원 도출(Sprint 3 Step 2): 유효 토큰이 있으면 collection_name/department 를
    **검증된 클레임**에서 가져온다(위조 불가). 없으면 요청 파라미터로 폴백(데모).
    응답의 tools_used 는 근거 배지, identity 는 어떤 신원으로 처리됐는지 시연용.
    스트리밍은 추후(agent.invoke 가 현재 블로킹).
    """
    if user.is_authenticated:
        # 토큰 클레임 우선 — 클라가 못 속임. org_id 는 Step 1 처럼 collection 로 매핑.
        collection_name = user.org_id or req.collection_name
        department = user.department
    else:
        collection_name = req.collection_name
        department = resolve_department(req.department)

    ctx = ToolContext(
        claude=ClaudeClient(),
        rag=RAGEngine(collection_name=collection_name),
        kg=_get_or_create_kg(collection_name),
        domain_context=req.domain_context,
        collection_name=collection_name,
        department=department,
    )
    result = run_agent(req.message, ctx)
    return {
        "text":       result["text"],
        "tools_used": result["tools_used"],
        "iterations": result["iterations"],
        "identity": {
            "authenticated": user.is_authenticated,
            "department":    department,
            "collection":    collection_name,
        },
    }
