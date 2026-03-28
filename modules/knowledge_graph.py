"""
[역할] 지식 그래프 구축 및 HTML 시각화
문서에서 추출된 엔티티·관계를 그래프로 구성하고 인터랙티브 HTML로 렌더링합니다.
  - build_from_claude_extraction() : Claude가 추출한 엔티티·관계 JSON → NetworkX 그래프
  - build_from_schema_json()       : SCHEMA_DEFINITION.json의 테이블·FK 구조 → 그래프
  - build_from_csv_schema()        : CSV 스키마 정보 → 그래프 (2-pass: 노드 먼저, FK 엣지 나중)
  - build_from_python_graph_data() : Python AST 추출 결과(함수·클래스·import) → 그래프
  - render_html()                  : pyvis로 인터랙티브 그래프 HTML 파일 생성
  - query_by_id()                  : 특정 노드의 연결 노드·엣지 조회
"""
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
            col_names = [c["name"] for c in columns if c.get("name")]
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
                columns=col_names,
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
        fallback_color = colors.get("default", "#6B7280")

        # 타입별 시각 설정 (color는 entity_colors보다 우선)
        _NODE_VISUAL: Dict[str, dict] = {
            "master_table": {"shape": "diamond", "color": "#7C3AED", "size": 52},
            "fact_table":   {"shape": "ellipse",  "color": "#2563EB", "size": 46},
            "csv_table":    {"shape": "dot",      "color": "#0D9488", "size": 36},
            "file":         {"shape": "box",      "size": 32},
            "class":        {"shape": "ellipse",  "size": 28},
            "function":     {"shape": "dot",      "size": 22},
            "method":       {"shape": "dot",      "size": 18},
            "module":       {"shape": "triangle", "size": 20},
        }

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
              "gravitationalConstant": -80,
              "centralGravity": 0.008,
              "springLength": 200,
              "springConstant": 0.05
            },
            "solver": "forceAtlas2Based",
            "stabilization": {"iterations": 200}
          },
          "edges": {
            "arrows": {"to": {"enabled": true, "scaleFactor": 0.8}},
            "color": {"color": "#888888"},
            "smooth": {"type": "curvedCW", "roundness": 0.1}
          },
          "nodes": {
            "font": {"size": 14, "strokeWidth": 3, "strokeColor": "#1a1a2e"},
            "borderWidth": 2
          },
          "interaction": {
            "zoomSpeed": 0.3,
            "hover": true
          }
        }
        """)

        # JS에 넘길 노드 메타데이터
        node_meta: Dict[str, Any] = {}

        for node_id, attrs in self.graph.nodes(data=True):
            node_type = attrs.get("type", "default")
            vis_cfg = _NODE_VISUAL.get(node_type, {})

            color = vis_cfg.get("color") or colors.get(node_type, fallback_color)
            size  = vis_cfg.get("size", 26)
            shape = vis_cfg.get("shape", "dot")
            title = attrs.get("title") or f"유형: {node_type}"

            net.add_node(
                node_id,
                label=attrs.get("label", node_id),
                title=title,
                color=color,
                size=size,
                shape=shape,
            )

            # 노드 정보 패널용 메타데이터 수집
            node_meta[node_id] = {
                "type": node_type,
                "columns":   attrs.get("columns", []),
                "col_types": attrs.get("col_types", {}),
                "fk_cols":   attrs.get("fk_cols", []),
                "out_edges": [
                    {"to": t,  "rel": self.graph[node_id][t].get("relation", "")}
                    for t in self.graph.successors(node_id)
                ],
                "in_edges": [
                    {"from": s, "rel": self.graph[s][node_id].get("relation", "")}
                    for s in self.graph.predecessors(node_id)
                ],
            }

        for src, tgt, attrs in self.graph.edges(data=True):
            relation = attrs.get("relation", "")
            # label은 비워두고 title(hover 툴팁)에만 관계명 표시 → 글씨 겹침 방지
            net.add_edge(src, tgt, label="", title=relation)

        os.makedirs(os.path.dirname(GRAPH_OUTPUT_PATH), exist_ok=True)
        net.save_graph(GRAPH_OUTPUT_PATH)
        self._inject_ui(GRAPH_OUTPUT_PATH, node_meta)
        return GRAPH_OUTPUT_PATH

    @staticmethod
    def _inject_ui(html_path: str, node_meta: Dict[str, Any]) -> None:
        """줌 컨트롤 + 노드 클릭 정보 패널을 pyvis HTML에 주입합니다."""
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
        except OSError:
            return

        node_meta_json = json.dumps(node_meta, ensure_ascii=False)

        css_html = """
<style>
/* ── 줌 컨트롤 ── */
#kg-zoom{position:fixed;top:10px;right:10px;z-index:9999;display:flex;
  align-items:center;gap:5px;background:rgba(15,15,35,.9);
  border:1px solid #555;border-radius:8px;padding:5px 10px;font-family:sans-serif;}
#kg-zoom button{background:#2a2a4a;color:#eee;border:1px solid #666;
  border-radius:5px;width:28px;height:28px;font-size:16px;cursor:pointer;
  line-height:1;transition:background .15s;}
#kg-zoom button:hover:not(:disabled){background:#3a3a6a;}
#kg-zoom button:disabled{opacity:.3;cursor:default;}
#kg-zoom span{color:#ccc;font-size:12px;min-width:38px;text-align:center;}
/* ── 노드 정보 패널 ── */
#np{position:fixed;top:55px;right:10px;width:255px;max-height:78%;
  overflow-y:auto;background:rgba(8,8,28,.95);border:1px solid #4a5568;
  border-radius:10px;padding:13px;z-index:9990;display:none;
  font-family:sans-serif;color:#e2e8f0;font-size:12px;}
#np h3{color:#fff;font-size:13px;margin:0 0 5px;word-break:break-all;padding-right:18px;}
#np .tag{display:inline-block;padding:2px 8px;border-radius:4px;
  font-size:10px;margin-bottom:8px;color:#fff;font-weight:700;}
#np .sec{color:#64748b;font-size:10px;text-transform:uppercase;
  letter-spacing:.06em;margin:9px 0 3px;font-weight:700;border-top:1px solid #1e293b;padding-top:7px;}
#np .col{padding:1px 0;font-size:11px;color:#cbd5e1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
#np .col.fk{color:#fbbf24;}
#np .edg{padding:2px 0;font-size:11px;}
#np .out{color:#6ee7b7;}
#np .inp{color:#93c5fd;}
#np .rel{color:#475569;font-size:10px;}
#np .none{color:#475569;font-size:11px;font-style:italic;}
#np-x{position:absolute;top:7px;right:9px;background:none;border:none;
  color:#64748b;cursor:pointer;font-size:17px;line-height:1;padding:0;}
#np-x:hover{color:#e2e8f0;}
</style>
<div id="kg-zoom">
  <button id="kg-zi" onclick="kgZoom(1)" title="확대">+</button>
  <span id="kg-lbl">100%</span>
  <button id="kg-zo" onclick="kgZoom(-1)" title="축소">\u2212</button>
</div>
<div id="np">
  <button id="np-x" onclick="document.getElementById('np').style.display='none'">\u00d7</button>
  <h3 id="np-name"></h3>
  <span id="np-tag" class="tag"></span>
  <div class="sec">컬럼</div>
  <div id="np-cols"></div>
  <div class="sec">연결된 테이블</div>
  <div id="np-edges"></div>
</div>
"""

        js_template = """
<script>
var _KZL=[.7,.8,.9,1.0],_KZI=3;
function kgZoom(d){
  _KZI=Math.max(0,Math.min(_KZL.length-1,_KZI+d));
  var s=_KZL[_KZI];
  if(typeof network!=='undefined')
    network.moveTo({scale:s,animation:{duration:200,easingFunction:'easeInOutQuad'}});
  document.getElementById('kg-lbl').textContent=Math.round(s*100)+'%';
  document.getElementById('kg-zi').disabled=(_KZI>=_KZL.length-1);
  document.getElementById('kg-zo').disabled=(_KZI<=0);
}
var NM=__NODE_META__;
var TC={'master_table':'#7C3AED','fact_table':'#2563EB','csv_table':'#0D9488'};
var TL={'master_table':'MASTER','fact_table':'FACT','csv_table':'CSV'};
function showNode(id){
  var m=NM[id]||{};
  document.getElementById('np-name').textContent=id;
  var tg=document.getElementById('np-tag');
  tg.style.background=TC[m.type]||'#6B7280';
  tg.textContent=TL[m.type]||m.type||'NODE';
  var cols=m.columns||[],fks=m.fk_cols||[],ct=m.col_types||{};
  var ch='';
  if(!cols.length){ch='<div class="none">정보 없음</div>';}
  else{
    cols.slice(0,25).forEach(function(c){
      var f=fks.indexOf(c)>=0;
      var t=ct[c]?'<span class="rel"> ('+ct[c]+')</span>':'';
      ch+='<div class="col'+(f?' fk':'')+'">'+c+t+(f?' \uD83D\uDD11':'')+'</div>';
    });
    if(cols.length>25)ch+='<div class="none">\u2026 외 '+(cols.length-25)+'개</div>';
  }
  document.getElementById('np-cols').innerHTML=ch;
  var oe=m.out_edges||[],ie=m.in_edges||[],eh='';
  oe.forEach(function(e){eh+='<div class="edg out">\u2192 '+e.to+(e.rel?'<span class="rel"> ('+e.rel+')</span>':'')+'</div>';});
  ie.forEach(function(e){eh+='<div class="edg inp">\u2190 '+e.from+(e.rel?'<span class="rel"> ('+e.rel+')</span>':'')+'</div>';});
  if(!eh)eh='<div class="none">없음</div>';
  document.getElementById('np-edges').innerHTML=eh;
  document.getElementById('np').style.display='block';
}
(function poll(){
  if(typeof network!=='undefined'){
    network.on('zoom',function(e){document.getElementById('kg-lbl').textContent=Math.round(e.scale*100)+'%';});
    network.on('click',function(p){if(p.nodes.length>0)showNode(p.nodes[0]);});
  }else{setTimeout(poll,150);}
})();
</script>
"""
        js = js_template.replace("__NODE_META__", node_meta_json)
        inject = css_html + js

        if "</body>" in html:
            html = html.replace("</body>", inject + "\n</body>")
        else:
            html += inject

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

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

        # 테이블 이름 접두사로 타입 자동 감지
        tn_upper = table_name.upper()
        if tn_upper.startswith("MST_"):
            node_type = "master_table"
        elif tn_upper.startswith("FACT_"):
            node_type = "fact_table"
        else:
            node_type = "csv_table"

        tooltip = (
            f"[{node_type}]\n"
            f"컬럼 수: {len(columns)}\n"
            f"컬럼: {', '.join(columns[:10])}{'...' if len(columns) > 10 else ''}\n"
            f"FK 후보: {', '.join(fk_candidates) if fk_candidates else '없음'}"
        )
        self.graph.add_node(
            table_name,
            label=table_name,
            type=node_type,
            title=tooltip,
            columns=columns,
            col_types=col_types,
            fk_cols=fk_candidates,
        )

        # FK 후보 컬럼을 다른 테이블과 연결
        all_names = {n.lower(): n for n in (all_table_names or list(self.graph.nodes))}
        for fk_col in fk_candidates:
            # fk_col 이름에서 참조 테이블 추론: PRODUCT_ID → product → MST_PRODUCT
            for suffix in ("_id", "_no", "_code", "_cd", "_num", "_key", "_seq", "_pk",
                           "번호", "코드"):
                if fk_col.lower().endswith(suffix):
                    ref_candidate = fk_col[: -len(suffix)].lower()
                    if not ref_candidate:
                        break
                    # 1) 정확 매칭
                    # 2) 복수형(s)
                    # 3) 테이블명이 후보를 포함하거나(MST_PRODUCT ⊃ product) 역방향
                    matched_ref = None
                    if ref_candidate in all_names:
                        matched_ref = all_names[ref_candidate]
                    elif ref_candidate + "s" in all_names:
                        matched_ref = all_names[ref_candidate + "s"]
                    else:
                        for tname_lower, tname in all_names.items():
                            if (ref_candidate in tname_lower
                                    or tname_lower.startswith(ref_candidate)
                                    or ref_candidate.startswith(tname_lower)):
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
