-- ============================================================
-- Supabase pgvector 마이그레이션 — RAG 문서 청크 저장
-- Supabase SQL Editor에서 실행하세요.
-- 사전 조건: Supabase 프로젝트에 pgvector extension 활성화
-- ============================================================

-- 1. pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. 문서 청크 테이블 생성
--    embedding 차원: 384 (paraphrase-multilingual-MiniLM-L12-v2)
DROP TABLE IF EXISTS "document_chunks" CASCADE;
CREATE TABLE "document_chunks" (
  "id"              TEXT PRIMARY KEY,
  "collection_name" TEXT NOT NULL,
  "filename"        TEXT NOT NULL,
  "chunk_index"     INTEGER NOT NULL,
  "content"         TEXT NOT NULL,
  "embedding"       vector(384)
);

-- 3. 인덱스
CREATE INDEX IF NOT EXISTS document_chunks_collection_idx
  ON document_chunks (collection_name);

-- ivfflat 코사인 유사도 인덱스 (데이터 수천 건 이상일 때 효과적)
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
  ON document_chunks USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- 4. RLS
ALTER TABLE "document_chunks" ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all" ON "document_chunks" FOR ALL USING (true) WITH CHECK (true);

-- 5. 벡터 유사도 검색 RPC 함수
CREATE OR REPLACE FUNCTION match_document_chunks(
  query_embedding vector(384),
  collection       TEXT,
  match_count      INTEGER DEFAULT 5
)
RETURNS TABLE (
  id          TEXT,
  content     TEXT,
  filename    TEXT,
  chunk_index INTEGER,
  similarity  FLOAT
)
LANGUAGE sql STABLE
AS $$
  SELECT
    id,
    content,
    filename,
    chunk_index,
    1 - (embedding <=> query_embedding) AS similarity
  FROM document_chunks
  WHERE collection_name = collection
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;
