-- ============================================================
-- 부서별 가중치 RAG 마이그레이션 — retrieval_profiles (Sprint 3, Step 1)
-- Supabase SQL Editor에서 실행하세요.
--
-- 설계(Codex): "같은 지식그래프, 부서별 렌즈."
--   부서마다 검색 가중치 프로파일을 두고, 검색 '시점'에 재랭킹한다(사전계산 X).
--   community_weight : 커뮤니티(개념 묶음) 요약 전반의 비중
--   node_type_boost  : KG 노드 타입별 부스트 (예: {"fact_table":1.6})
--   → 타입이 있는 신호(커뮤니티/KG)에만 적용. 문서 청크(타입 없음)는 미가중.
--
-- 인증 전(Step 1) 임시: org_id 자리에 collection_name 을 사용한다(Step 2에서 JWT org_id 로 교체).
-- 재실행 안전: DROP 하지 않고 스키마만 보장 + 시드는 upsert.
-- ============================================================

CREATE TABLE IF NOT EXISTS "retrieval_profiles" (
  "org_id"           TEXT  NOT NULL,          -- 임시: collection_name (Step 2: JWT org_id)
  "department"       TEXT  NOT NULL,
  "community_weight" FLOAT NOT NULL DEFAULT 1.0,
  "node_type_boost"  JSONB NOT NULL DEFAULT '{}'::jsonb,
  "updated_at"       TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY ("org_id", "department")
);

ALTER TABLE "retrieval_profiles" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all" ON "retrieval_profiles";
CREATE POLICY "Allow all" ON "retrieval_profiles" FOR ALL USING (true) WITH CHECK (true);

-- ── 데모 시드 (beauty 샘플 = collection_name 'domain_sample') ──────────────────
-- 영업부: 거래·매출 팩트 테이블 중시 / 마스터는 낮춤
-- 재고부: 제품·공급사 마스터 + 원장(csv) 중시 / 팩트는 낮춤
INSERT INTO "retrieval_profiles" ("org_id", "department", "community_weight", "node_type_boost")
VALUES
  ('domain_sample', '영업부', 1.2, '{"fact_table": 1.6, "master_table": 0.9}'::jsonb),
  ('domain_sample', '재고부', 1.0, '{"master_table": 1.5, "csv_table": 1.2, "fact_table": 0.9}'::jsonb)
ON CONFLICT ("org_id", "department") DO UPDATE SET
  "community_weight" = EXCLUDED."community_weight",
  "node_type_boost"  = EXCLUDED."node_type_boost",
  "updated_at"       = now();
