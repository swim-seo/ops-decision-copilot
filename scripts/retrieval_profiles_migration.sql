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
--
-- 부스트 스프레드 튜닝(실데이터 검증): 초기값(fact 1.6/master 0.9)은 커뮤니티 간
-- base 의미 유사도 격차보다 약해 top 순위를 못 바꿨음. 강한 스프레드(2.5/0.5)로
-- 조정하니 '애매한 질문'에서 부서별로 top 커뮤니티가 갈리고(영업부→매출, 재고부→공급망),
-- '명확한 질문'에선 base 유사도가 정상적으로 지배함.
-- 주의: community_weight 는 프로파일 내 모든 커뮤니티에 동일하게 곱해져 커뮤니티 간
-- 순위에는 영향 없음(소스 간 병합 대비 스케일용). 순위를 가르는 건 node_type_boost.
INSERT INTO "retrieval_profiles" ("org_id", "department", "community_weight", "node_type_boost")
VALUES
  ('domain_sample', '영업부', 1.2, '{"fact_table": 2.5, "master_table": 0.5}'::jsonb),
  ('domain_sample', '재고부', 1.0, '{"master_table": 2.5, "csv_table": 1.5, "fact_table": 0.5}'::jsonb)
ON CONFLICT ("org_id", "department") DO UPDATE SET
  "community_weight" = EXCLUDED."community_weight",
  "node_type_boost"  = EXCLUDED."node_type_boost",
  "updated_at"       = now();
