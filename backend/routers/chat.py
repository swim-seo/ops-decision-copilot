from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from modules import chat_copilot
from modules.rag_engine import RAGEngine
from modules.claude_client import ClaudeClient
from backend.routers.upload import _get_or_create_kg

router = APIRouter()


class ChatRequest(BaseModel):
    message:         str
    collection_name: str = "domain_docs"
    domain_context:  str = ""
    stream:          bool = True


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
