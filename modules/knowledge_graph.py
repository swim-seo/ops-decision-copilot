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

    def build_from_schema_json(self, schema: dict) -> bool:
        """
        SCHEMA_DEFINITION.json 구조를 지식 그래프로 변환합니다.

        - tables   → 노드 (table_name, table_type, description, PK 컬럼)
        - relationships → 엣지 (join_key를 label로 표시)

        schema 형식:
        {
          "tables": [{"table_name": "...", "table_type": "...", "description": "...", "columns": [...]}],
          "relationships": [{"from": "...", "to": "...", "join_key": "...", "relation": "JOIN"}]
        }
        """
        tables = schema.get("tables", [])
        relationships = schema.get("relationships", [])

        if not tables and not relationships:
            return False

        for table in tables:
            table_name = table.get("table_name", "")
            if not table_name:
                continue
            table_type = table.get("table_type", "default")
            description = table.get("description", "")
            columns = table.get("columns", [])
            pk_cols = [c["name"] for c in columns if c.get("pk")]
            tooltip = (
                f"[{table_type}]\n"
                f"{description}\n"
                f"PK: {', '.join(pk_cols) if pk_cols else '없음'}\n"
                f"컬럼 수: {len(columns)}"
            )
            self.graph.add_node(
                table_name,
                label=table_name,
                type=table_type,
                title=tooltip,
            )

        for rel in relationships:
            src = rel.get("from", "")
            tgt = rel.get("to", "")
            join_key = rel.get("join_key", "")
            if src and tgt:
                self.graph.add_edge(src, tgt, relation=join_key)

        return True

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

        _type_size = {"fact_table": 45, "master_table": 35}

        for node_id, attrs in self.graph.nodes(data=True):
            node_type = attrs.get("type", "default")
            color = colors.get(node_type, fallback_color)
            title = attrs.get("title") or f"유형: {node_type}"
            size = _type_size.get(node_type, 25)
            net.add_node(
                node_id,
                label=attrs.get("label", node_id),
                title=title,
                color=color,
                size=size,
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

    def build_from_python_ast(self, graph_data: dict) -> bool:
        """Python AST에서 추출한 노드/엣지를 그래프에 추가합니다."""
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        if not nodes:
            return False

        for node in nodes:
            node_id = node.get("id", "")
            if node_id:
                self.graph.add_node(
                    node_id,
                    label=node.get("label", node_id),
                    type=node.get("type", "default"),
                )

        for edge in edges:
            src = edge.get("source", "")
            tgt = edge.get("target", "")
            if src and tgt:
                self.graph.add_edge(src, tgt, relation=edge.get("relation", "관련"))

        return True

    def build_from_csv_schema(self, schema: dict, all_table_names: list = None) -> bool:
        """CSV 스키마에서 테이블 노드와 FK 관계 엣지를 추가합니다."""
        table_name = schema.get("table_name", "")
        if not table_name:
            return False

        columns = schema.get("columns", [])
        fk_candidates = schema.get("fk_candidates", [])
        col_types = schema.get("col_types", {})

        pk_cols = [c for c in columns if c.lower() in ("id", f"{table_name.lower()}_id")]
        tooltip = (
            f"[CSV 테이블]\n"
            f"컬럼 수: {len(columns)}\n"
            f"컬럼: {', '.join(columns[:10])}{'...' if len(columns) > 10 else ''}\n"
            f"FK 후보: {', '.join(fk_candidates) if fk_candidates else '없음'}"
        )
        self.graph.add_node(
            table_name,
            label=table_name,
            type="csv_table",
            title=tooltip,
        )

        # FK 후보 컬럼을 다른 테이블과 연결
        all_names = {n.lower(): n for n in (all_table_names or list(self.graph.nodes))}
        for fk_col in fk_candidates:
            # fk_col 이름에서 참조 테이블 추론: order_id → order/orders, product_no → product/products
            for suffix in ("_id", "_no", "_code", "_num", "_key", "_seq", "_pk",
                           "번호", "코드"):
                if fk_col.lower().endswith(suffix):
                    ref_candidate = fk_col[: -len(suffix)].lower()
                    # 정확 매칭 → 복수형(s) → 접두 매칭
                    matched_ref = None
                    if ref_candidate in all_names:
                        matched_ref = all_names[ref_candidate]
                    elif ref_candidate + "s" in all_names:
                        matched_ref = all_names[ref_candidate + "s"]
                    else:
                        for tname_lower, tname in all_names.items():
                            if tname_lower.startswith(ref_candidate) or ref_candidate.startswith(tname_lower):
                                matched_ref = tname
                                break
                    if matched_ref and matched_ref != table_name:
                        self.graph.add_edge(table_name, matched_ref, relation=fk_col)
                    break

        return True

    def query_by_id(self, query: str) -> Dict[str, Any]:
        """부품번호·상품번호 등 키워드로 연결된 모든 노드 정보를 반환합니다."""
        query_lower = query.lower()
        matched = [n for n in self.graph.nodes if query_lower in n.lower()]

        result: Dict[str, Any] = {
            "matched_nodes": [],
            "connected_nodes": [],
            "edges": [],
        }

        visited_nodes = set()
        for node in matched:
            attrs = dict(self.graph.nodes[node])
            attrs["id"] = node
            result["matched_nodes"].append(attrs)
            visited_nodes.add(node)

        for node in matched:
            for neighbor in list(self.graph.successors(node)):
                if neighbor not in visited_nodes:
                    visited_nodes.add(neighbor)
                    n_attrs = dict(self.graph.nodes[neighbor])
                    n_attrs["id"] = neighbor
                    result["connected_nodes"].append(n_attrs)
                edge_data = self.graph.get_edge_data(node, neighbor) or {}
                result["edges"].append({
                    "from": node,
                    "to": neighbor,
                    "relation": edge_data.get("relation", ""),
                })
            for neighbor in list(self.graph.predecessors(node)):
                if neighbor not in visited_nodes:
                    visited_nodes.add(neighbor)
                    n_attrs = dict(self.graph.nodes[neighbor])
                    n_attrs["id"] = neighbor
                    result["connected_nodes"].append(n_attrs)
                edge_data = self.graph.get_edge_data(neighbor, node) or {}
                result["edges"].append({
                    "from": neighbor,
                    "to": node,
                    "relation": edge_data.get("relation", ""),
                })

        return result

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
