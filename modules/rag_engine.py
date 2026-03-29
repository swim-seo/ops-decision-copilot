"""
[역할] RAG(검색 증강 생성) 엔진
문서 청크를 벡터로 변환해 ChromaDB에 저장하고, 질문과 유사한 청크를 검색합니다.
  - add_documents()  : 텍스트 청크 → 임베딩 → ChromaDB 저장
  - search()         : 질문 텍스트 → 유사 청크 TOP-K 반환 (Claude 컨텍스트로 전달)
  - clear()          : 컬렉션 초기화
  - get_stats()      : 저장된 문서 수 등 현황 조회
도메인별로 별도 컬렉션(collection_name)을 사용해 데이터가 섞이지 않습니다.
"""
import uuid
from typing import List, Dict, Any

import chromadb
from chromadb.utils import embedding_functions

from config import VECTOR_DB_PATH, DEFAULT_COLLECTION_NAME, EMBEDDING_MODEL, TOP_K_RESULTS
from modules.document_parser import chunk_text


class RAGEngine:
    def __init__(self, collection_name: str = DEFAULT_COLLECTION_NAME):
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"},
        )

    def delete_document(self, filename: str) -> None:
        """특정 파일의 청크를 모두 삭제합니다 (재업로드 전 중복 방지용)."""
        try:
            existing = self.collection.get(where={"filename": filename})
            if existing and existing.get("ids"):
                self.collection.delete(ids=existing["ids"])
        except Exception:
            pass

    def add_document(self, text: str, filename: str) -> int:
        """문서를 청킹하여 벡터 DB에 저장합니다.
        같은 파일이 이미 있으면 기존 청크를 삭제하고 재삽입합니다."""
        self.delete_document(filename)  # 중복 방지
        chunks = chunk_text(text)
        if not chunks:
            return 0

        ids = [f"{filename}_{i}_{uuid.uuid4().hex[:8]}" for i in range(len(chunks))]
        metadatas = [{"filename": filename, "chunk_index": i} for i in range(len(chunks))]

        self.collection.add(documents=chunks, ids=ids, metadatas=metadatas)
        return len(chunks)

    def query(self, question: str, n_results: int = TOP_K_RESULTS) -> List[Dict[str, Any]]:
        """질문과 유사한 청크를 검색합니다."""
        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_texts=[question],
            n_results=min(n_results, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        hits = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            hits.append(
                {
                    "text": doc,
                    "filename": meta.get("filename", "알 수 없음"),
                    "chunk_index": meta.get("chunk_index", 0),
                    "score": round(1 - dist, 4),  # cosine similarity
                }
            )
        return hits

    def get_context(self, question: str) -> str:
        """질문에 대한 컨텍스트 문자열을 반환합니다."""
        hits = self.query(question)
        if not hits:
            return ""
        parts = []
        for i, h in enumerate(hits, 1):
            parts.append(f"[출처 {i}: {h['filename']}]\n{h['text']}")
        return "\n\n---\n\n".join(parts)

    def document_count(self) -> int:
        return self.collection.count()

    def delete_collection(self):
        """컬렉션을 초기화합니다."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"},
        )
