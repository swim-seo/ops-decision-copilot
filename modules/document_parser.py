"""
[역할] 문서 파싱 및 텍스트 청킹
업로드된 파일에서 텍스트를 추출하고 RAG에 적합한 크기로 분할합니다.
  - parse_file()             : PDF·DOCX·TXT·MD·CSV·PY → 텍스트 추출
  - extract_csv_schema()     : CSV 컬럼 구조·FK 후보·샘플 데이터 추출
  - extract_python_graph_data(): Python AST 파싱 → 함수·클래스·import 관계 추출 (KG용)
  - chunk_text()             : 긴 텍스트를 오버랩 청크로 분할 (RAG 인덱싱용)
"""
import ast
import csv
import io
import re
from typing import Dict, List, Any

import pypdf as PyPDF2  # pypdf>=4.0.0 (PyPDF2 대체, API 호환)
import docx


def parse_file(uploaded_file) -> str:
    """Streamlit UploadedFile 객체에서 텍스트를 추출합니다."""
    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        return _parse_pdf(uploaded_file)
    elif filename.endswith(".docx"):
        return _parse_docx(uploaded_file)
    elif filename.endswith((".txt", ".md")):
        return uploaded_file.read().decode("utf-8")
    elif filename.endswith(".py"):
        return uploaded_file.read().decode("utf-8")
    elif filename.endswith(".csv"):
        raw = uploaded_file.read().decode("utf-8", errors="replace")
        schema = extract_csv_schema(uploaded_file.name, raw)
        return _csv_schema_to_text(schema)
    else:
        raise ValueError(f"지원하지 않는 파일 형식입니다: {filename}")


# ── CSV 파싱 ──────────────────────────────────────────────────────────────────

_FK_SUFFIXES = ("_id", "_no", "_code", "_cd", "_num", "_key", "_seq", "_pk", "번호", "코드")


def extract_csv_schema(filename: str, raw_text: str) -> Dict[str, Any]:
    """CSV 파일에서 컬럼 구조와 FK 후보를 추출합니다."""
    reader = csv.DictReader(io.StringIO(raw_text))
    headers = list(reader.fieldnames or [])

    rows = []
    for i, row in enumerate(reader):
        rows.append(row)
        if i >= 4:
            break

    # FK 후보: _id, _no, 번호, 코드 등으로 끝나는 컬럼
    fk_candidates = [
        h for h in headers
        if any(h.lower().endswith(s) for s in _FK_SUFFIXES)
    ]

    # 컬럼 타입 추론 (숫자/문자/날짜)
    col_types: Dict[str, str] = {}
    for h in headers:
        sample_vals = [r.get(h, "") for r in rows if r.get(h, "").strip()]
        col_types[h] = _infer_col_type(h, sample_vals)

    table_name = re.sub(r"\.csv$", "", filename, flags=re.IGNORECASE)

    return {
        "table_name": table_name,
        "columns": headers,
        "col_types": col_types,
        "fk_candidates": fk_candidates,
        "sample_rows": rows[:3],
        "total_cols": len(headers),
    }


def _infer_col_type(col_name: str, vals: List[str]) -> str:
    col_lower = col_name.lower()
    if any(kw in col_lower for kw in ("date", "time", "dt", "일자", "날짜", "일시")):
        return "datetime"
    if not vals:
        return "string"
    numeric = sum(1 for v in vals if re.fullmatch(r"-?\d+(\.\d+)?", v.replace(",", "")))
    if numeric >= len(vals) * 0.8:
        return "numeric"
    return "string"


def _csv_schema_to_text(schema: Dict[str, Any]) -> str:
    lines = [f"[테이블] {schema['table_name']}"]
    for col in schema["columns"]:
        ctype = schema["col_types"].get(col, "string")
        fk_mark = " (FK후보)" if col in schema["fk_candidates"] else ""
        lines.append(f"  컬럼: {col} ({ctype}){fk_mark}")
    if schema["fk_candidates"]:
        lines.append(f"\nFK 후보 컬럼: {', '.join(schema['fk_candidates'])}")
    if schema["sample_rows"]:
        lines.append("\n샘플 데이터:")
        for row in schema["sample_rows"]:
            lines.append("  " + str(dict(row)))
    return "\n".join(lines)


# ── Python AST 파싱 ────────────────────────────────────────────────────────────

def extract_python_graph_data(source: str, filename: str) -> Dict[str, Any]:
    """Python 소스에서 함수/클래스/import 관계를 KG 노드·엣지로 추출합니다."""
    nodes: List[Dict] = []
    edges: List[Dict] = []
    seen_ids: set = set()

    def _add_node(node_id: str, label: str, node_type: str):
        if node_id not in seen_ids:
            nodes.append({"id": node_id, "label": label, "type": node_type})
            seen_ids.add(node_id)

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"nodes": [], "edges": []}

    file_id = re.sub(r"\.py$", "", filename)
    _add_node(file_id, file_id, "file")

    # import 관계
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split(".")[0]
                _add_node(mod, mod, "module")
                edges.append({"source": file_id, "target": mod, "relation": "imports"})
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mod = node.module.split(".")[0]
                _add_node(mod, mod, "module")
                edges.append({"source": file_id, "target": mod, "relation": "imports"})

    # 클래스/함수/메서드
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            _add_node(node.name, node.name, "class")
            edges.append({"source": file_id, "target": node.name, "relation": "defines"})
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    meth_id = f"{node.name}.{item.name}"
                    _add_node(meth_id, item.name, "method")
                    edges.append({"source": node.name, "target": meth_id, "relation": "has_method"})
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            # 최상위 함수만 (클래스 메서드 제외)
            _add_node(node.name, node.name, "function")
            edges.append({"source": file_id, "target": node.name, "relation": "defines"})

    return {"nodes": nodes, "edges": edges}


def _parse_pdf(file) -> str:
    reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _parse_docx(file) -> str:
    doc = docx.Document(io.BytesIO(file.read()))
    return "\n".join(para.text for para in doc.paragraphs)


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
    """텍스트를 오버랩이 있는 청크로 분할합니다."""
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # 문장/단락 경계에서 자르기
        if end < len(text):
            for sep in ["\n\n", "\n", ". ", "。", " "]:
                idx = chunk.rfind(sep)
                if idx > chunk_size // 2:
                    chunk = chunk[: idx + len(sep)]
                    end = start + idx + len(sep)
                    break

        chunk = chunk.strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap

    return chunks
