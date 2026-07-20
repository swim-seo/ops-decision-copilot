# Codex Design Review — Target Platform Architecture

**Date:** 2026-07-18
**Reviewer:** Codex CLI (gpt-5.2-codex, sandbox read-only)
**Topic:** Review of `target-platform-architecture.md` — 4 unresolved questions from section 7 + overall risk review
**Context:** One-person portfolio project targeting a posting emphasizing RAG optimization, Agentic Workflow, MCP/FastMCP, Function Calling. Stack: Next.js 15 + FastAPI + `modules/` + Supabase pgvector + in-memory NetworkX KG. Only the feature layer exists (no auth/tenancy/persistence/async/observability).

## Questions posed
- Q1. LangGraph vs hand-rolled agent loop — which better serves the portfolio?
- Q2. KG persistence: normalized node/edge tables vs whole-graph JSON blob?
- Q3. Department-weighted RAG: query-time vs precomputed index (by scale + threshold)?
- Q4. Async queue: Supabase queue table (FOR UPDATE SKIP LOCKED) vs Celery+Redis?
- Q5. Overall risk review, esp. sprint ordering (AI orchestration before persistence/auth).

---

## Codex Response

규칙 로드 완료, DESIGN.md 확인 완료. 바로 답변드립니다.

**Q1.** LangGraph 채택이 **순이득**입니다. 포지션이 "Agentic Workflow"와 프레임워크 경험을 명시했으므로, LangGraph는 리뷰어에게 즉시 신호를 주고("실제 현업 스택 경험"), 데모 품질도 올라갑니다. 핸드롤 루프는 원리 이해를 보여줄 수 있지만 포트폴리오에서의 신호가 약하고, 유지보수 부담 대비 차별화가 작습니다.

**Q2.** 지금 접근 패턴(도메인 전체 그래프 로드 + 가끔 2‑hop)이면 **도메인 단위 JSON blob 저장**이 맞습니다. 단순화/속도/비용이 유리하고 네트워크 비용도 예측 가능합니다. **전환 임계**: 단일 도메인 그래프가 **~200k nodes / 1M edges** 이상이거나, 2‑hop 질의가 **QPS 10+**로 늘어 읽기 최적화가 필요해지면 정규화 테이블+인덱스로 전환하세요.

**Q3.** 현재는 **Query‑time 가중치 계산**이 정답입니다. 부서별 프로파일 수가 적고, 가중치가 자주 바뀔 수 있어 선계산은 운영 부담만 늘립니다. **전환 임계**: **노드 1M+** 또는 **QPS 20+**에서 지연이 눈에 띄면, "부서별 재가중치된 스코어 뷰/테이블"을 **비동기 재계산**으로 도입하세요.

**Q4.** 포트폴리오 맥락에서는 **Supabase 큐 테이블로 충분**합니다. "적절한 간결함 + 실무 패턴"을 보여주면서 오버엔지니어링을 피할 수 있습니다. **전환 임계**: 동시 작업자 **5+**, 재시도/지연 큐/워크플로우가 복잡해지거나, 처리량 **수백 jobs/일** 이상이면 Celery+Redis로 이동하세요.

**Q5.** **리스크/누락**:
- Sprint 1의 LangGraph 데모가 **재시작 시 KG 유실**로 불안정해질 수 있음 → 데모 신뢰도 하락 위험.
- **RAG 평가(precision/recall, latency, cost)**, **idempotency**(KG 재빌드/중복 업서트), **비용 가드레일**, **테스트 전략**이 설계에 없음.
- 보안 측면에서 RLS off + 서비스 키 사용은 **신뢰성 데모에 치명적**(최소한 "왜 unsafe인지, 어떻게 고칠지" 명시 필요).

**Verdict:** **Sprint 1부터 진행해도 SOUND**입니다 — 단, Sprint 1 범위에 **고정 데모 데이터 자동 재로딩(bootstrap)**을 포함해 데모 안정성만 확보하세요.
