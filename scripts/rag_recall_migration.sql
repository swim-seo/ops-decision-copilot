-- RAG 검색 recall 복구
--
-- 증상: 브리핑 4개 카드 중 3개가 항상 "관련 내용을 찾을 수 없습니다" 로 나왔다.
--       match_document_chunks 가 HTTP 200 에 0행을 돌려주는데, 함수에는 임계값이
--       없고 테이블에는 데이터가 있었다.
--
-- 원인: document_chunks_embedding_idx 가 ivfflat(lists = 100) 인데 실제 청크가
--       500여 개뿐이라 리스트 하나에 ~5행씩 들어간다. ivfflat.probes 기본값은 1 이라
--       스캔이 리스트 한 개(약 5행)만 보고, 거기에 collection_name 필터가 걸리면
--       남는 행이 0 이 되는 일이 흔하다. 같은 질문을 정확 검색으로 돌리면
--       유사도 0.5 대의 정상 결과가 나온다 — 인덱스 recall 문제였다.
--
-- 조치: 이 규모에서는 인덱스가 손해다(500행 정확 스캔은 1ms 미만). 인덱스를 내리고,
--       함수에는 probes 를 박아 두어 나중에 인덱스를 되살려도 recall 이 무너지지 않게 한다.
--
-- 재실행 안전: DROP ... IF EXISTS + CREATE OR REPLACE.

DROP INDEX IF EXISTS document_chunks_embedding_idx;

-- 데이터가 충분히 커지면(대략 수만 행 이상) 아래를 되살린다.
-- 기준: lists ≈ 행수/1000, probes ≈ sqrt(lists). 지금 값(lists=100)은 500행 기준
-- 과분할이라 recall 이 무너졌다.
--
--   CREATE INDEX document_chunks_embedding_idx
--     ON document_chunks USING ivfflat (embedding vector_cosine_ops)
--     WITH (lists = 100);

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
-- 인덱스가 없으면 무시되고, 되살렸을 때만 효과가 있다.
SET ivfflat.probes = 10
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
