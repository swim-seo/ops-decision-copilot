"""
[역할] RAG(검색 증강 생성) 엔진 — Supabase pgvector 기반
문서 청크를 벡터로 변환해 Supabase에 저장하고, 질문과 유사한 청크를 검색합니다.
  - add_document()     : 텍스트 → 임베딩 → Supabase document_chunks 저장
  - query()            : 질문 → 코사인 유사도 TOP-K 청크 반환 (Claude 컨텍스트로 전달)
  - delete_document()  : 특정 파일의 청크 전체 삭제 (재업로드 중복 방지)
  - delete_collection(): 컬렉션 전체 청크 삭제
  - document_count()   : 저장된 청크 수 조회

도메인별로 collection_name 컬럼으로 데이터를 격리합니다.
Supabase 미연결 시 add/delete는 에러를 발생시키고, query는 빈 리스트를 반환합니다.
"""
import json
import logging
import uuid
from typing import List, Dict, Any

import requests
from sentence_transformers import SentenceTransformer

from config import DEFAULT_COLLECTION_NAME, EMBEDDING_MODEL, TOP_K_RESULTS
from modules.document_parser import chunk_text
import modules.supabase_client as _sb

logger = logging.getLogger(__name__)

_TABLE = "document_chunks"
_RPC   = "match_document_chunks"


class RAGEngine:
    def __init__(self, collection_name: str = DEFAULT_COLLECTION_NAME):
        self.collection_name = collection_name
        self._model = SentenceTransformer(EMBEDDING_MODEL)

    # ── 내부 헬퍼 ────────────────────────────────────────────────────────────

    def _embed(self, text: str) -> List[float]:
        """텍스트 → 정규화된 임베딩 벡터 (384차원)"""
        return self._model.encode(text, normalize_embeddings=True).tolist()

    def _file_filter(self, filename: str) -> dict:
        return {
            "collection_name": f"eq.{self.collection_name}",
            "filename":        f"eq.{filename}",
        }

    def _collection_filter(self) -> dict:
        return {"collection_name": f"eq.{self.collection_name}"}

    # ── 공개 API ─────────────────────────────────────────────────────────────

    def delete_document(self, filename: str) -> None:
        """특정 파일의 청크를 모두 삭제합니다 (재업로드 전 중복 방지용)."""
        _sb.delete_rows(_TABLE, self._file_filter(filename))

    def add_document(self, text: str, filename: str) -> int:
        """문서를 청킹·임베딩하여 Supabase에 저장합니다.
        같은 파일이 이미 있으면 기존 청크를 삭제하고 재삽입합니다."""
        self.delete_document(filename)

        chunks = chunk_text(text)
        if not chunks:
            return 0

        if not _sb.is_connected():
            raise ConnectionError("Supabase에 연결되지 않았습니다. 벡터 저장 불가.")

        records = []
        for i, chunk in enumerate(chunks):
            records.append({
                "id":              f"{filename}_{i}_{uuid.uuid4().hex[:8]}",
                "collection_name": self.collection_name,
                "filename":        filename,
                "chunk_index":     i,
                "content":         chunk,
                "embedding":       self._embed(chunk),
            })

        # Supabase REST API는 vector 컬럼에 JSON 배열을 자동 캐스팅합니다
        headers = {
            **_sb._headers(),
            "Prefer": "resolution=merge-duplicates",
        }
        r = requests.post(
            f"{_sb._url}/rest/v1/{_TABLE}",
            headers=headers,
            data=json.dumps(records, ensure_ascii=False),
            timeout=60,
        )
        if r.status_code not in (200, 201, 204):
            raise RuntimeError(f"벡터 저장 실패 (HTTP {r.status_code}): {r.text}")

        logger.info("RAG: %d chunks stored for '%s'", len(records), filename)
        return len(records)

    def query(self, question: str, n_results: int = TOP_K_RESULTS) -> List[Dict[str, Any]]:
        """질문과 유사한 청크를 검색합니다."""
        if not _sb.is_connected():
            return []

        rows = _sb.rpc(_RPC, {
            "query_embedding": self._embed(question),
            "collection":      self.collection_name,
            "match_count":     n_results,
        })
        if not rows:
            return []

        return [
            {
                "text":        row["content"],
                "filename":    row["filename"],
                "chunk_index": row["chunk_index"],
                "score":       round(float(row["similarity"]), 4),
            }
            for row in rows
        ]

    def get_context(self, question: str) -> str:
        """질문에 대한 컨텍스트 문자열을 반환합니다."""
        hits = self.query(question)
        if not hits:
            return ""
        parts = [f"[출처 {i}: {h['filename']}]\n{h['text']}" for i, h in enumerate(hits, 1)]
        return "\n\n---\n\n".join(parts)

    def document_count(self) -> int:
        """이 컬렉션에 저장된 청크 수를 반환합니다."""
        return _sb.count_rows(_TABLE, self._collection_filter())

    def delete_collection(self) -> None:
        """컬렉션의 청크를 전부 삭제합니다."""
        _sb.delete_rows(_TABLE, self._collection_filter())
