-- ============================================================
-- GraphRAG 마이그레이션 — 커뮤니티 요약 저장 테이블
-- Supabase SQL Editor에서 실행하세요.
-- 사전 조건: vector_migration.sql이 먼저 실행되어 있어야 합니다.
-- ============================================================

-- 커뮤니티 요약 테이블
DROP TABLE IF EXISTS "community_summaries" CASCADE;
CREATE TABLE "community_summaries" (
  "id"              TEXT PRIMARY KEY,
  "collection_name" TEXT NOT NULL,
  "community_id"    INTEGER NOT NULL,
  "node_list"       TEXT NOT NULL,   -- JSON 배열 (노드 ID 목록)
  "summary"         TEXT NOT NULL,   -- Claude가 생성한 커뮤니티 요약
  "embedding"       vector(384)      -- 요약 임베딩 (유사도 검색용)
);

CREATE INDEX IF NOT EXISTS community_summaries_collection_idx
  ON community_summaries (collection_name);

CREATE INDEX IF NOT EXISTS community_summaries_embedding_idx
  ON community_summaries USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 50);

ALTER TABLE "community_summaries" ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all" ON "community_summaries" FOR ALL USING (true) WITH CHECK (true);

-- 커뮤니티 요약 유사도 검색 RPC 함수
CREATE OR REPLACE FUNCTION match_community_summaries(
  query_embedding vector(384),
  collection       TEXT,
  match_count      INTEGER DEFAULT 3
)
RETURNS TABLE (
  id            TEXT,
  community_id  INTEGER,
  node_list     TEXT,
  summary       TEXT,
  similarity    FLOAT
)
LANGUAGE sql STABLE
AS $$
  SELECT
    id,
    community_id,
    node_list,
    summary,
    1 - (embedding <=> query_embedding) AS similarity
  FROM community_summaries
  WHERE collection_name = collection
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;
