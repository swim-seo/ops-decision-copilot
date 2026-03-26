"""지식 그래프 모듈 - NetworkX + pyvis 기반 엔티티 관계 시각화"""
import json
import os
import re
from typing import Dict, List, Any

import networkx as nx
from pyvis.network import Network

from config import DEFAULT_ENTITY_COLORS, GRAPH_OUTPUT_PATH


class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def build_from_claude_json(self, json_str: str) -> bool:
        """
        Claude가 추출한 JSON 형식의 엔티티/관계를 그래프에 추가합니다.
        JSON 형식:
        {
          "nodes": [{"id": "...", "label": "...", "type": "..."}],
          "edges": [{"source": "...", "target": "...", "relation": "..."}]
        }
        """
        # 마크다운 코드 블록(```json ... ```) 우선 추출
        code_block = re.search(r"```(?:json)?\s*([\s\S]*?)```", json_str)
        if code_block:
            candidate = code_block.group(1).strip()
        else:
            match = re.search(r"\{[\s\S]*\}", json_str)
            if not match:
                return False
            candidate = match.group()

        # 후행 쉼표 제거 (예: [...,] {…,}) — Claude가 자주 생성하는 비표준 JSON
        candidate = re.sub(r",\s*([}\]])", r"\1", candidate)

        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            return False

        for node in data.get("nodes", []):
            node_id = node.get("id", "")
            if node_id:
                self.graph.add_node(
                    node_id,
                    label=node.get("label", node_id),
                    type=node.get("type", "default"),
                )

        for edge in data.get("edges", []):
            src = edge.get("source", "")
            tgt = edge.get("target", "")
            rel = edge.get("relation", "관련")
            if src and tgt:
                self.graph.add_edge(src, tgt, relation=rel)

        return True

    def render_html(self, entity_colors: Dict[str, str] = None) -> str:
        """pyvis HTML을 생성하고 파일 경로를 반환합니다.

        Args:
            entity_colors: 엔티티 유형별 색상 딕셔너리. None이면 DEFAULT_ENTITY_COLORS 사용.
        """
        if len(self.graph.nodes) == 0:
            return ""

        colors = entity_colors or DEFAULT_ENTITY_COLORS
        fallback_color = colors.get("default", "#9E9E9E")

        net = Network(
            height="580px",
            width="100%",
            bgcolor="#1a1a2e",
            font_color="#ffffff",
            directed=True,
        )
        net.set_options("""
        {
          "physics": {
            "forceAtlas2Based": {
              "gravitationalConstant": -50,
              "centralGravity": 0.01,
              "springLength": 120
            },
            "solver": "forceAtlas2Based",
            "stabilization": {"iterations": 150}
          },
          "edges": {
            "arrows": {"to": {"enabled": true, "scaleFactor": 0.8}},
            "color": {"color": "#aaaaaa"},
            "font": {"size": 11, "color": "#dddddd"}
          },
          "nodes": {
            "font": {"size": 13},
            "borderWidth": 2
          }
        }
        """)

        for node_id, attrs in self.graph.nodes(data=True):
            node_type = attrs.get("type", "default")
            color = colors.get(node_type, fallback_color)
            net.add_node(
                node_id,
                label=attrs.get("label", node_id),
                title=f"유형: {node_type}",
                color=color,
                size=25,
            )

        for src, tgt, attrs in self.graph.edges(data=True):
            net.add_edge(src, tgt, label=attrs.get("relation", ""))

        os.makedirs(os.path.dirname(GRAPH_OUTPUT_PATH), exist_ok=True)
        net.save_graph(GRAPH_OUTPUT_PATH)
        return GRAPH_OUTPUT_PATH

    def get_stats(self) -> Dict[str, Any]:
        return {
            "nodes": len(self.graph.nodes),
            "edges": len(self.graph.edges),
            "entity_types": self._count_types(),
        }

    def _count_types(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for _, attrs in self.graph.nodes(data=True):
            t = attrs.get("type", "default")
            counts[t] = counts.get(t, 0) + 1
        return counts

    def clear(self):
        self.graph.clear()


def build_entity_extraction_prompt(entity_types_description: str) -> str:
    """도메인 엔티티 유형을 반영한 추출 프롬프트를 생성합니다."""
    return f"""당신은 문서에서 지식 그래프를 구축하는 전문가입니다.
아래 문서에서 엔티티(노드)와 관계(엣지)를 추출하세요.

엔티티 유형:
{entity_types_description}

반드시 아래 JSON 형식으로만 답변하세요 (다른 텍스트 없이):
{{
  "nodes": [
    {{"id": "고유ID", "label": "표시명", "type": "엔티티유형"}}
  ],
  "edges": [
    {{"source": "노드ID1", "target": "노드ID2", "relation": "관계설명"}}
  ]
}}

---
문서 내용:
{{document}}
"""
