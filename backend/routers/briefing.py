from fastapi import APIRouter
from pydantic import BaseModel
from modules.claude_client import ClaudeClient, TOKENS
from modules.rag_engine import RAGEngine

router = APIRouter()

# query 는 검색용, ask 는 Claude 지시용이다. 검색 쿼리는 키워드 나열이 아니라
# 문장으로 둔다 — 임베딩 모델이 문장으로 학습돼 있어 키워드 나열은 어떤 청크와도
# 어중간하게 닮고, 그만큼 상위 결과가 흔들린다.
BRIEFING_CARDS = [
    {
        "id":    "summary",
        "label": "핵심 요약",
        "color": "blue",
        "query": "이 데이터는 전체적으로 무엇을 담고 있는가",
        "ask":   "업로드된 데이터/문서의 핵심 내용을 3~5줄로 요약해줘.",
    },
    {
        "id":    "risk",
        "label": "주요 리스크",
        "color": "red",
        "query": "문제가 되고 있는 항목, 위험 신호, 기준을 벗어난 비정상 수치",
        "ask":   "업로드된 데이터/문서에서 발견되는 주요 리스크나 문제점을 구체적으로 알려줘.",
    },
    {
        "id":    "insight",
        "label": "인사이트",
        "color": "green",
        "query": "눈에 띄는 변화나 추세, 다른 항목과 크게 차이 나는 값",
        "ask":   "업로드된 데이터/문서에서 주목할 만한 인사이트나 기회 요소를 알려줘.",
    },
    {
        "id":    "action",
        "label": "추천 액션",
        "color": "amber",
        "query": "먼저 처리해야 할 항목과 조치가 필요한 대상",
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
        # 도메인 컨텍스트는 프롬프트에만 쓰고 검색어에는 섞지 않는다. 실측해 보면
        # 도메인명을 앞에 붙일수록 컬럼명이 늘어선 헤더 청크 쪽으로 끌려가서,
        # 정작 필요한 이상치 행(재고 CRITICAL/WARNING)이 상위에서 밀린다.
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
