#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data/uploads/ 의 텍스트 문서를 Supabase document_chunks에 인덱싱합니다.
실행: python scripts/index_docs.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env", override=True)

from modules.rag_engine import RAGEngine
from config import DEFAULT_COLLECTION_NAME

UPLOADS_DIR = ROOT / "data" / "uploads"

def run():
    rag = RAGEngine(collection_name=DEFAULT_COLLECTION_NAME)
    files = list(UPLOADS_DIR.glob("*.txt")) + list(UPLOADS_DIR.glob("*.md"))

    if not files:
        print(f"[INDEX] {UPLOADS_DIR} 에 텍스트 파일이 없습니다.")
        return

    print(f"[INDEX] {len(files)}개 파일 인덱싱 시작...")
    for f in files:
        text = f.read_text(encoding="utf-8")
        n = rag.add_document(text, f.name)
        print(f"  [OK] {f.name} -> {n}개 청크 저장")

    total = rag.document_count()
    print(f"\n[INDEX] 완료. 전체 청크 수: {total}")

if __name__ == "__main__":
    run()
