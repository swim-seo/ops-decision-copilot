from fastapi import APIRouter
from pydantic import BaseModel
from modules.claude_client import ClaudeClient, TOKENS
from modules.rag_engine import RAGEngine

router = APIRouter()

BRIEFING_CARDS = [
    {
        "id":    "summary",
        "label": "핵심 요약",
        "color": "blue",
        "query": "전체 내용 핵심 요약",
        "ask":   "업로드된 데이터/문서의 핵심 내용을 3~5줄로 요약해줘.",
    },
    {
        "id":    "risk",
        "label": "주요 리스크",
        "color": "red",
        "query": "리스크 문제 이슈 위험",
        "ask":   "업로드된 데이터/문서에서 발견되는 주요 리스크나 문제점을 구체적으로 알려줘.",
    },
    {
        "id":    "insight",
        "label": "인사이트",
        "color": "green",
        "query": "성과 트렌드 기회 개선",
        "ask":   "업로드된 데이터/문서에서 주목할 만한 인사이트나 기회 요소를 알려줘.",
    },
    {
        "id":    "action",
        "label": "추천 액션",
        "color": "amber",
        "query": "액션 결정 다음단계 개선방안",
        "ask":   "지금 당장 취해야 할 행동이나 우선순위 높은 과제를 3가지 이내로 제안해줘.",
    },
]


class BriefingRequest(BaseModel):
    collection_name: str = "domain_docs"
    domain_context:  str = ""


@router.post("/generate")
def generate_briefing(req: BriefingRequest):
    claude = ClaudeClient()
    rag    = RAGEngine(collection_name=req.collection_name)
    cards  = []

    for card in BRIEFING_CARDS:
        context = rag.get_context(card["query"])
        if not context:
            answer = "업로드된 데이터가 없거나 관련 내용을 찾을 수 없습니다."
        else:
            prompt = (
                f"당신은 운영 데이터 분석 전문가입니다.\n"
                f"{f'도메인 컨텍스트: {req.domain_context}' if req.domain_context else ''}\n\n"
                f"[참고 데이터]\n{context}\n\n"
                f"{card['ask']}\n\n"
                f"3~5문장으로 간결하게 한국어로 답변하세요. ~~취소선~~, ~~이중물결표~~ 사용 금지."
            )
            try:
                answer = claude.generate(prompt, max_tokens=TOKENS["briefing"])
            except Exception as e:
                answer = f"분석 중 오류: {e}"

        cards.append({
            "id":     card["id"],
            "label":  card["label"],
            "color":  card["color"],
            "answer": answer,
        })

    return {"cards": cards}
