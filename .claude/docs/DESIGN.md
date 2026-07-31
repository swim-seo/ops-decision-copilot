# Project Design Document

> This document tracks design decisions made during conversations.
> Updated automatically by the `design-tracker` skill.

## Overview

<!-- Project purpose and goals -->

## Architecture

<!-- System structure, components, data flow -->

```
[Component diagram or description here]
```

## Implementation Plan

### Patterns & Approaches

<!-- Design patterns, architectural approaches -->

| Pattern | Purpose | Notes |
|---------|---------|-------|
| | | |

### Libraries & Roles

<!-- Libraries and their responsibilities -->

| Library | Role | Version | Notes |
|---------|------|---------|-------|
| | | | |

### Key Decisions

<!-- Important decisions and their rationale -->

| Decision | Rationale | Alternatives Considered | Date |
|----------|-----------|------------------------|------|
| `document_chunks` 의 ivfflat 인덱스를 내린다 | `lists=100` 에 청크가 500여 개뿐이라 리스트당 ~5행. `probes=1` 이 훑은 리스트에 `collection_name` 필터를 걸면 결과가 0 이 되는 일이 흔했고, 실제로 브리핑 4개 카드 중 3개가 항상 빈 응답이었다. 이 규모에서 정확 스캔은 1ms 미만이라 인덱스가 순손해 | `probes` 만 올리기(리스트당 5행이라 10 을 줘도 후보 50행 — 필터 뒤 여전히 부족) / 임계값 낮추기(원인이 임계값이 아니었음) | 2026-07-31 |
| 조인 키를 `join_key`·`join_keys` 로 따로 노출한다 | `relation` 하나에 스키마 FK 컬럼명과 문서 KG 의 서술어("관련")가 같이 담겨 의미가 겹쳤다. 소비자가 필드만 보고 조인 키인지 알 수 없다 | `relation` 재사용(의미 중복 유지) / 엣지 타입 필드 추가(소비자가 분기해야 함) | 2026-07-31 |
| 조인 키 조회는 매트릭스, 그래프는 군집 보기로 강등 | "이 팩트를 저 마스터에 무슨 키로 붙이나"는 조회형 질문이라 행×열 표가 정답이다. 노드-링크로는 한 번에 못 읽는다 | 그래프에 라벨만 더 붙이기(엣지 15개부터 라벨이 겹침) | 2026-07-31 |
| 스키마 그래프를 계층 배치 + physics off 로 고정 | 힘기반 배치는 열 개만 넘어도 실뭉치가 되고 열 때마다 그림이 달라 "어제 본 그 자리"가 없다. 방향 기준 계층이면 팩트가 위, 참조받는 마스터가 아래로 내려가 참조 깊이가 그대로 읽힌다 | 힘기반 유지 + 간격 확대(2026-07-30 에 시도했고 여전히 엉킴) | 2026-07-31 |
| 브리핑 검색어를 문장으로, 도메인 컨텍스트는 검색에 섞지 않음 | 임베딩 모델이 문장 학습이라 키워드 나열은 모든 청크와 어중간하게 닮는다. 도메인명을 앞에 붙이면 컬럼명이 늘어선 헤더 청크로 끌려가 리스크 카드가 이상치 행을 놓쳤다(실측) | 도메인 프리픽스 적용(측정 후 되돌림) | 2026-07-31 |
| 라벨은 본문서체, `font-data` 는 ASCII 전용 | IBM Plex Mono 를 latin 서브셋으로 받아 한글 글리프가 없다. 한글 라벨이 시스템 mono 로 떨어져 전각 칸에 갇혔다 | mono 폴백 체인에만 한글 서체 추가(공백은 mono 글리프가 있어 폭이 어긋남) | 2026-07-31 |

## TODO

<!-- Features to implement -->

- [ ] 

## Open Questions

<!-- Unresolved issues, things to investigate -->

- [ ] 

## Changelog

| Date | Changes |
|------|---------|
| | Initial |
