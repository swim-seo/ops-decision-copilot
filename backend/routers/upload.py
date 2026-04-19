import os
import tempfile
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from typing import List
from modules.document_parser import parse_file, extract_csv_schema
from modules.rag_engine import RAGEngine
from modules.knowledge_graph import KnowledgeGraph
from modules.claude_client import ClaudeClient
from domains import get_preset

router = APIRouter()

_graphs: dict[str, KnowledgeGraph] = {}

DATA_DIR = Path(__file__).parent.parent.parent / "data"

SAMPLES = {
    "beauty": {
        "label": "뷰티 / 이커머스",
        "description": "제품, 공급사, 채널, 매출, 재고, 발주, 반품 데이터",
        "path": DATA_DIR / "beauty",
        "domain": "beauty",
        "keywords": ["뷰티", "beauty", "화장품", "이커머스"],
    },
    "supply_chain": {
        "label": "공급망 / 재고",
        "description": "부품, 공급업체, 창고, 발주 데이터",
        "path": DATA_DIR / "supply_chain",
        "domain": "supply_chain",
        "keywords": ["공급망", "supply", "재고", "물류"],
    },
    "energy": {
        "label": "에너지",
        "description": "발전소 사용량, 청구, 장애 데이터",
        "path": DATA_DIR / "energy",
        "domain": "energy",
        "keywords": ["에너지", "energy", "발전"],
    },
    "manufacturing": {
        "label": "제조 / 생산",
        "description": "생산 실적, 설비, 불량 데이터",
        "path": DATA_DIR / "manufacturing",
        "domain": "manufacturing",
        "keywords": ["제조", "manufacturing", "생산", "공장"],
    },
    "logistics": {
        "label": "물류 / 배송",
        "description": "배송 현황, 노선, 차량, 지연 데이터",
        "path": DATA_DIR / "logistics",
        "domain": "logistics",
        "keywords": ["물류", "logistics", "배송", "운송"],
    },
    "finance": {
        "label": "금융 / 회계",
        "description": "거래 내역, 성과, 리스크 데이터",
        "path": DATA_DIR / "finance",
        "domain": "finance",
        "keywords": ["금융", "finance", "회계", "투자"],
    },
}


def _get_or_create_kg(collection_name: str) -> KnowledgeGraph:
    if collection_name not in _graphs:
        _graphs[collection_name] = KnowledgeGraph()
    return _graphs[collection_name]


def _domain_context(domain_name: str) -> tuple[str, str]:
    """(context_str, entity_types_desc) 반환"""
    preset = get_preset(domain_name)
    terms = ", ".join(preset.get("terminology", [])[:10])
    focus = ", ".join(preset.get("analysis_focus", []))
    context = f"도메인: {domain_name}\n주요 용어: {terms}\n분석 포커스: {focus}"

    entity_types = preset.get("entity_types", {})
    _hints = {
        "person": "사람, 담당자", "organization": "조직, 회사",
        "product": "제품, SKU", "supplier": "공급업체",
        "process": "프로세스", "issue": "문제, 이슈",
        "decision": "결정 사항", "metric": "지표, KPI",
    }
    etype_desc = "\n".join(
        f"- {k}: {_hints.get(k, k)}" for k in entity_types
    )
    return context, etype_desc


async def _process_file(path: str, filename: str, rag, kg, claude, domain_name: str):
    suffix = os.path.splitext(filename)[1].lower()
    context_str, etype_desc = _domain_context(domain_name)

    if suffix == ".csv":
        import pandas as pd
        df = pd.read_csv(path)
        with open(path, encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()
        schema = extract_csv_schema(filename, raw_text)
        kg.build_from_csv_schema(schema)
        text = df.to_string(index=False)
    elif suffix == ".json" and filename.upper() == "SCHEMA_DEFINITION.JSON":
        import json
        with open(path) as f:
            data = json.load(f)
        kg.build_from_schema_json(data)
        text = json.dumps(data, ensure_ascii=False)
    else:
        if suffix in (".txt", ".md"):
            with open(path, encoding="utf-8", errors="ignore") as f:
                text = f.read()
        elif suffix == ".pdf":
            import pypdf
            reader = pypdf.PdfReader(path)
            text = "\n".join(p.extract_text() or "" for p in reader.pages)
        elif suffix == ".docx":
            import docx as _docx
            doc = _docx.Document(path)
            text = "\n".join(p.text for p in doc.paragraphs)
        elif suffix == ".py":
            with open(path, encoding="utf-8", errors="ignore") as f:
                text = f.read()
        else:
            text = ""
        if text:
            from modules.prompt_loader import load_prompt
            try:
                prompt = load_prompt(
                    "kg_extraction",
                    domain_context=context_str,
                    entity_types=etype_desc,
                    document_text=text[:3000],
                )
                import json
                raw = claude.generate(prompt, max_tokens=1000)
                data = json.loads(raw[raw.find("{"):raw.rfind("}")+1])
                kg.build_from_claude_json(data)
            except Exception:
                pass

    chunks = 0
    if text:
        chunks = rag.add_document(text, filename)
    return chunks


@router.post("/files")
async def upload_files(
    files: List[UploadFile] = File(...),
    domain_name: str = Form("generic"),
    collection_name: str = Form("domain_docs"),
):
    rag    = RAGEngine(collection_name=collection_name)
    kg     = _get_or_create_kg(collection_name)
    claude = ClaudeClient()
    results = []

    for file in files:
        suffix = os.path.splitext(file.filename)[1].lower()
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        try:
            chunks = await _process_file(tmp_path, file.filename, rag, kg, claude, domain_name)
            results.append({"filename": file.filename, "chunks": chunks, "status": "ok"})
        except Exception as e:
            results.append({"filename": file.filename, "error": str(e), "status": "error"})
        finally:
            os.unlink(tmp_path)

    return {"files": results}


class SampleRequest(BaseModel):
    sample_id: str
    collection_name: str = "domain_sample"


@router.post("/sample")
async def load_sample(req: SampleRequest):
    sample = SAMPLES.get(req.sample_id)
    if not sample:
        from fastapi import HTTPException
        raise HTTPException(404, f"샘플 없음: {req.sample_id}")

    sample_path: Path = sample["path"]
    domain_name: str  = sample["domain"]

    rag    = RAGEngine(collection_name=req.collection_name)
    kg     = _get_or_create_kg(req.collection_name)
    claude = ClaudeClient()
    results = []

    for filepath in sorted(sample_path.iterdir()):
        if not filepath.is_file():
            continue
        try:
            chunks = await _process_file(str(filepath), filepath.name, rag, kg, claude, domain_name)
            results.append({"filename": filepath.name, "chunks": chunks, "status": "ok"})
        except Exception as e:
            results.append({"filename": filepath.name, "error": str(e), "status": "error"})

    return {
        "files": results,
        "collection_name": req.collection_name,
        "domain": domain_name,
    }


@router.get("/samples")
def list_samples():
    return [
        {
            "id": k,
            "label": v["label"],
            "description": v["description"],
            "keywords": v.get("keywords", []),
        }
        for k, v in SAMPLES.items()
    ]
