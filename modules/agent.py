"""
[역할] AI 오케스트레이션 층 — LangGraph 에이전트 (Sprint 1, Step 2)

chat_copilot.detect_route()의 if-else 규칙 라우팅을 대체한다.
LLM이 agent_tools.TOOL_SCHEMAS 중 필요한 툴을 스스로 선택·실행하며
plan → act → reflect 루프를 돌고, 더 이상 툴이 필요 없으면 최종 답변(synthesize).

그래프 구조 (ReAct 스타일):

        ┌──────────────┐
  질문 →│  call_model  │  ← LLM이 툴 선택 (plan/reflect)
        └──────┬───────┘
       tool_use? │
        ┌────────┴─────────┐
    있음│                   │없음
        ▼                   ▼
  ┌───────────┐           END  (final_text = 답변, synthesize)
  │ run_tools │  ← run_tool() 실행 (act)
  └─────┬─────┘
        └──▶ call_model 로 결과 반환 (반복)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, TypedDict

from langgraph.graph import StateGraph, END

from modules.agent_tools import TOOL_SCHEMAS, ToolContext, run_tool

logger = logging.getLogger(__name__)

# 무한 툴 호출 방지 — 비용 가드레일 (Codex 리뷰 지적 대응)
MAX_ITERATIONS = 5

_SYSTEM = (
    "당신은 운영 의사결정을 돕는 AI 어시스턴트입니다. "
    "주어진 툴로 문서·지식그래프·데이터를 조회해 근거 기반으로 답하세요.\n"
    "- 관계/원인/영향 질문 → search_graph\n"
    "- 문서 근거가 필요 → search_documents\n"
    "- 수치/랭킹/재고/추이 → analyze_data\n"
    "- 전반 요약/리스크/추천액션 → get_briefing\n"
    "필요하면 여러 툴을 순차로 사용하고, 근거가 충분해지면 한국어로 종합 답변하세요. "
    "툴로 얻은 근거가 없으면 추측하지 말고 자료가 없다고 답하세요."
)


class AgentState(TypedDict):
    """그래프 노드 사이를 흐르는 상태."""
    messages:   List[Dict[str, Any]]   # anthropic 메시지 누적 (user/assistant/tool_result)
    ctx:        ToolContext            # 요청별 의존성 (rag/kg/claude/...)
    iterations: int
    tool_trace: List[str]              # 사용한 툴 이름 기록 (UI 근거 배지·관측용)
    final_text: str


# ── 노드 ───────────────────────────────────────────────────────────────────────

def _call_model(state: AgentState) -> Dict[str, Any]:
    """LLM에 현재 대화 + 툴 스키마를 넘겨 다음 행동을 받는다 [plan/reflect].

    응답에 tool_use 블록이 있으면 → run_tools 로 이어지고,
    text 만 있으면 → 그 text 가 최종 답변이 된다.
    """
    claude = state["ctx"].claude
    resp = claude.create_message(
        messages=state["messages"],
        tools=TOOL_SCHEMAS,
        system=_SYSTEM,
        max_tokens=2000,
    )

    # assistant 메시지를 dict 로 직렬화해 누적 (다음 턴에 그대로 재전송 가능한 형식)
    assistant_content = [block.model_dump() for block in resp.content]
    new_messages = state["messages"] + [
        {"role": "assistant", "content": assistant_content}
    ]

    # 최종 텍스트 후보 (툴 호출이 없을 때 이 값이 답변)
    text = "".join(b.text for b in resp.content if b.type == "text")

    return {
        "messages":   new_messages,
        "iterations": state["iterations"] + 1,
        "final_text": text,
    }


def _run_tools(state: AgentState) -> Dict[str, Any]:
    """직전 assistant 메시지의 tool_use 블록을 실행해 tool_result 로 되돌린다 [act]."""
    last_content = state["messages"][-1]["content"]
    tool_results: List[Dict[str, Any]] = []
    trace = list(state["tool_trace"])

    for block in last_content:
        if block.get("type") != "tool_use":
            continue
        name = block["name"]
        result = run_tool(state["ctx"], name, block.get("input", {}))
        trace.append(name)
        tool_results.append({
            "type":        "tool_result",
            "tool_use_id": block["id"],
            "content":     result,
        })

    new_messages = state["messages"] + [{"role": "user", "content": tool_results}]
    return {"messages": new_messages, "tool_trace": trace}


def _should_continue(state: AgentState) -> str:
    """tool_use 가 있으면 계속(run_tools), 없거나 한도 초과면 종료(END)."""
    if state["iterations"] >= MAX_ITERATIONS:
        logger.warning("에이전트 최대 반복(%d) 도달 — 강제 종료", MAX_ITERATIONS)
        return END
    last_content = state["messages"][-1]["content"]
    has_tool_use = any(b.get("type") == "tool_use" for b in last_content)
    return "run_tools" if has_tool_use else END


# ── 그래프 빌드 ─────────────────────────────────────────────────────────────────

def build_agent():
    """상태 그래프를 조립해 컴파일된 에이전트를 반환한다."""
    g = StateGraph(AgentState)
    g.add_node("call_model", _call_model)
    g.add_node("run_tools", _run_tools)
    g.set_entry_point("call_model")
    g.add_conditional_edges(
        "call_model",
        _should_continue,
        {"run_tools": "run_tools", END: END},
    )
    g.add_edge("run_tools", "call_model")
    return g.compile()


# 컴파일된 그래프는 상태를 안 가지므로 모듈 싱글턴으로 재사용 (요청별 상태는 invoke 인자)
_AGENT = None


def get_agent():
    global _AGENT
    if _AGENT is None:
        _AGENT = build_agent()
    return _AGENT


def run_agent(question: str, ctx: ToolContext) -> Dict[str, Any]:
    """질문을 에이전트로 처리해 최종 답변 + 사용 툴 목록을 반환한다.

    Returns: {"text": str, "tools_used": list[str], "iterations": int}
    """
    from modules.chat_copilot import sanitize_input  # 프롬프트 인젝션 방어 재사용

    agent = get_agent()
    init: AgentState = {
        "messages":   [{"role": "user", "content": sanitize_input(question)}],
        "ctx":        ctx,
        "iterations": 0,
        "tool_trace": [],
        "final_text": "",
    }
    final = agent.invoke(init)
    return {
        "text":       final["final_text"] or "답변을 생성하지 못했습니다.",
        "tools_used": final["tool_trace"],
        "iterations": final["iterations"],
    }
