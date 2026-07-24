-- ============================================================
-- 비동기 잡 큐 마이그레이션 — jobs 테이블 + claim RPC (Sprint 4 ②)
-- Supabase SQL Editor에서 실행하세요.
--
-- 설계(Codex): Supabase 큐 테이블 + FOR UPDATE SKIP LOCKED 워커. 인프라 추가 없음.
-- PostgREST 는 SELECT FOR UPDATE 를 직접 못 하므로 claim 은 plpgsql RPC 로 감싼다.
-- ============================================================

CREATE TABLE IF NOT EXISTS "jobs" (
  "id"           TEXT PRIMARY KEY,
  "job_type"     TEXT        NOT NULL,
  "payload"      JSONB       NOT NULL DEFAULT '{}'::jsonb,
  "status"       TEXT        NOT NULL DEFAULT 'pending',   -- pending|processing|done|failed
  "attempts"     INTEGER     NOT NULL DEFAULT 0,
  "max_attempts" INTEGER     NOT NULL DEFAULT 3,
  "error"        TEXT,
  "result"       JSONB,
  "created_at"   TIMESTAMPTZ NOT NULL DEFAULT now(),
  "started_at"   TIMESTAMPTZ,
  "finished_at"  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS jobs_status_created_idx ON jobs (status, created_at);

ALTER TABLE "jobs" ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all" ON "jobs";
CREATE POLICY "Allow all" ON "jobs" FOR ALL USING (true) WITH CHECK (true);

-- ── 잡 클레임 RPC — 경쟁 안전(FOR UPDATE SKIP LOCKED) ──────────────────────────
-- pending 잡 1개를 원자적으로 집어 processing 으로 전환(attempts+1, started_at 기록).
-- 크래시로 processing 에 갇힌 잡은 lease_seconds 경과 시 재수거(중복 처리 방지 겸 복구).
-- UPDATE...WHERE id=(SELECT...FOR UPDATE SKIP LOCKED LIMIT 1) 는 단일문이라 원자적.
CREATE OR REPLACE FUNCTION claim_next_job(lease_seconds INTEGER DEFAULT 300)
RETURNS SETOF jobs
LANGUAGE sql
AS $$
  UPDATE jobs
  SET status     = 'processing',
      started_at = now(),
      attempts   = attempts + 1
  WHERE id = (
    SELECT id FROM jobs
    WHERE status = 'pending'
       OR (status = 'processing'
           AND started_at < now() - make_interval(secs => lease_seconds))
    ORDER BY created_at
    FOR UPDATE SKIP LOCKED
    LIMIT 1
  )
  RETURNING *;
$$;
