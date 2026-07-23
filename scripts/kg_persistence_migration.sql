-- ============================================================
-- KG 영속성 마이그레이션 — 지식그래프 JSON blob 저장 테이블 (Sprint 2)
-- Supabase SQL Editor에서 실행하세요.
--
-- 설계(Codex Q2): 도메인(collection)당 그래프를 통째로 JSON blob 1행에 저장.
--   조회 패턴(도메인당 그래프 전체 로드 + 간헐 2-hop)에 부합, 단순·저비용.
--   전환 기준: 단일 그래프 >~20만 노드/100만 엣지 또는 2-hop ~10 QPS+ →
--             정규화 노드/엣지 테이블 + 인덱스로 이전.
--
-- 주의: 영속 데이터이므로 DROP 하지 않는다(재실행 안전). 스키마 변경만 반영.
-- ============================================================

CREATE TABLE IF NOT EXISTS "knowledge_graphs" (
  "collection_name" TEXT PRIMARY KEY,
  "graph_json"      JSONB       NOT NULL,   -- networkx node_link_data 직렬화 결과
  "node_count"      INTEGER     NOT NULL DEFAULT 0,
  "edge_count"      INTEGER     NOT NULL DEFAULT 0,
  "updated_at"      TIMESTAMPTZ NOT NULL DEFAULT now()  -- 캐시 정합성(버전) 체크용
);

ALTER TABLE "knowledge_graphs" ENABLE ROW LEVEL SECURITY;
-- 현재는 백엔드가 service key 로 접근(데모). Sprint 3 에서 org_id 기반 RLS 로 재작성 예정.
DROP POLICY IF EXISTS "Allow all" ON "knowledge_graphs";
CREATE POLICY "Allow all" ON "knowledge_graphs" FOR ALL USING (true) WITH CHECK (true);
