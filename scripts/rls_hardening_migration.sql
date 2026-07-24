-- ============================================================
-- RLS 하드닝 — 테넌트 격리 정책 (Sprint 3 Step 3)
--
-- ⚠️⚠️ 중요 — 이 정책들은 '현재 발동하지 않는다'.
--   백엔드가 Supabase secret key(sb_secret_...)로 접근하는데, secret key 는
--   RLS 를 통째로 우회한다(service_role 급). 따라서 실제 조직 격리는 서버 코드의
--   authorize_collection() (backend/auth.py) 이 강제한다.
--
--   그럼 왜 쓰는가? (defense-in-depth + 문서화된 의도)
--     1) '올바른 RLS 가 어떤 모습이어야 하는가'를 명시적으로 남긴다.
--     2) 향후 백엔드가 '사용자 JWT 경유' 읽기 경로로 전환하면(anon/publishable
--        key + 사용자 토큰), 이 정책들이 즉시 격리를 발동한다.
--     3) 누군가 실수로 anon key 로 접근해도 최소한의 방어선이 존재한다.
--
--   전제: 사용자 JWT 에 collection_name(또는 org_id) 클레임이 들어있어야 이 정책이
--         의미를 갖는다. 데모의 secret-key 경로에선 무관(우회).
-- ============================================================

-- ── collection_name 기반 테넌시 테이블 ────────────────────────────────────────
-- document_chunks (RAG 청크)
DROP POLICY IF EXISTS "Allow all" ON document_chunks;
DROP POLICY IF EXISTS "tenant_isolation" ON document_chunks;
CREATE POLICY "tenant_isolation" ON document_chunks FOR ALL
  USING      (collection_name = (auth.jwt() ->> 'collection_name'))
  WITH CHECK (collection_name = (auth.jwt() ->> 'collection_name'));

-- community_summaries (GraphRAG 요약)
DROP POLICY IF EXISTS "Allow all" ON community_summaries;
DROP POLICY IF EXISTS "tenant_isolation" ON community_summaries;
CREATE POLICY "tenant_isolation" ON community_summaries FOR ALL
  USING      (collection_name = (auth.jwt() ->> 'collection_name'))
  WITH CHECK (collection_name = (auth.jwt() ->> 'collection_name'));

-- knowledge_graphs (KG 영속 blob)
DROP POLICY IF EXISTS "Allow all" ON knowledge_graphs;
DROP POLICY IF EXISTS "tenant_isolation" ON knowledge_graphs;
CREATE POLICY "tenant_isolation" ON knowledge_graphs FOR ALL
  USING      (collection_name = (auth.jwt() ->> 'collection_name'))
  WITH CHECK (collection_name = (auth.jwt() ->> 'collection_name'));

-- ── org_id 기반 테넌시 테이블 ─────────────────────────────────────────────────
-- retrieval_profiles (부서 가중치 — org_id 로 격리)
DROP POLICY IF EXISTS "Allow all" ON retrieval_profiles;
DROP POLICY IF EXISTS "tenant_isolation" ON retrieval_profiles;
CREATE POLICY "tenant_isolation" ON retrieval_profiles FOR ALL
  USING      (org_id = (auth.jwt() ->> 'org_id'))
  WITH CHECK (org_id = (auth.jwt() ->> 'org_id'));

-- ============================================================
-- 롤백(데모로 되돌리기): 위 정책을 지우고 Allow all 로 복원
--   DROP POLICY IF EXISTS "tenant_isolation" ON <table>;
--   CREATE POLICY "Allow all" ON <table> FOR ALL USING (true) WITH CHECK (true);
-- (secret-key 경로에선 어느 쪽이든 백엔드 동작에 영향 없음)
-- ============================================================
