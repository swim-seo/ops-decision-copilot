"""
이커머스 재고관리 도메인 데모 데이터셋 생성기
출력: data/ 폴더에 CSV 5개 + SCHEMA_DEFINITION.json + LOGIC_DOCUMENT.txt
"""
import csv
import json
import os
import random

random.seed(42)
OUT = "./data"

# ── 마스터 데이터 정의 ────────────────────────────────────────────────────────

PRODUCTS = [
    ("P001", "무선 이어폰 프로",       "ELECTRONICS",  89000, 14, 10, "SUP002"),
    ("P002", "스마트워치 SE",          "ELECTRONICS", 249000, 21,  5, "SUP001"),
    ("P003", "노트북 파우치 15인치",   "ACCESSORIES",  35000,  7, 20, "SUP003"),
    ("P004", "USB-C 허브 7포트",       "ELECTRONICS",  65000, 14, 15, "SUP002"),
    ("P005", "블루투스 스피커 미니",   "ELECTRONICS",  79000, 14, 10, "SUP001"),
    ("P006", "스마트폰 케이스 투명",   "ACCESSORIES",  15000,  5, 50, "SUP003"),
    ("P007", "보조배터리 20000mAh",    "ELECTRONICS",  45000, 10, 20, "SUP002"),
    ("P008", "무선 충전기 15W",        "ELECTRONICS",  35000, 10, 20, "SUP001"),
]

SUPPLIERS = [
    ("SUP001", "테크파트너스(주)",      "한국",  7, 4.8, "tech@partners.co.kr"),
    ("SUP002", "글로벌소싱코리아",      "중국", 21, 4.2, "global@sourcing.cn"),
    ("SUP003", "한국전자부품(주)",      "한국",  5, 4.9, "hq@kecparts.co.kr"),
]

WAREHOUSES = [
    ("WH001", "서울 메인 물류센터", "경기도 이천시",      50000, "수도권"),
    ("WH002", "부산 물류센터",      "부산광역시 강서구",  30000, "영남"),
    ("WH003", "대전 물류센터",      "대전광역시 대덕구",  25000, "충청"),
]

MONTHS = ["2024-10", "2024-11", "2024-12"]

# 창고별 수요 가중치 (수도권 > 영남 > 충청)
WH_WEIGHT = {"WH001": 1.0, "WH002": 0.6, "WH003": 0.4}

# 월별 시즌 계수 (11~12월 연말 성수기)
MONTH_FACTOR = {"2024-10": 1.0, "2024-11": 1.3, "2024-12": 1.7}

# 제품별 기준 수요량
BASE_DEMAND = {
    "P001": 320, "P002": 180, "P003": 210,
    "P004": 150, "P005": 260, "P006": 480,
    "P007": 380, "P008": 290,
}

# 스냅샷 날짜 (월말)
SNAPSHOTS = ["2024-10-31", "2024-11-30", "2024-12-31"]


# ── 1. MST_PRODUCT ────────────────────────────────────────────────────────────
def write_mst_product():
    rows = []
    for p_no, p_name, cat, price, lead, moq, sup_cd in PRODUCTS:
        rows.append({
            "PRODUCT_NO":    p_no,
            "PRODUCT_NAME":  p_name,
            "CATEGORY_CD":   cat,
            "UNIT_PRICE":    price,
            "LEAD_TIME_DAY": lead,
            "MIN_ORDER_QTY": moq,
            "SUPPLIER_CD":   sup_cd,
        })
    _write_csv("MST_PRODUCT.csv", rows)
    print(f"  MST_PRODUCT.csv — {len(rows)}행")


# ── 2. MST_SUPPLIER ───────────────────────────────────────────────────────────
def write_mst_supplier():
    rows = []
    for s_cd, s_name, country, lead, score, email in SUPPLIERS:
        rows.append({
            "SUPPLIER_CD":        s_cd,
            "SUPPLIER_NAME":      s_name,
            "COUNTRY":            country,
            "LEAD_TIME_DAY":      lead,
            "RELIABILITY_SCORE":  score,
            "CONTACT_EMAIL":      email,
        })
    _write_csv("MST_SUPPLIER.csv", rows)
    print(f"  MST_SUPPLIER.csv — {len(rows)}행")


# ── 3. MST_WAREHOUSE ──────────────────────────────────────────────────────────
def write_mst_warehouse():
    rows = []
    for w_cd, w_name, loc, cap, region in WAREHOUSES:
        rows.append({
            "WAREHOUSE_CD":   w_cd,
            "WAREHOUSE_NAME": w_name,
            "LOCATION":       loc,
            "CAPACITY":       cap,
            "REGION":         region,
        })
    _write_csv("MST_WAREHOUSE.csv", rows)
    print(f"  MST_WAREHOUSE.csv — {len(rows)}행")


# ── 4. FACT_MONTHLY_DEMAND ────────────────────────────────────────────────────
def write_fact_monthly_demand():
    rows = []
    demand_id = 1
    # 누적 수요 추적 (재고 스냅샷 계산용)
    demand_map = {}

    for ym in MONTHS:
        mf = MONTH_FACTOR[ym]
        for p_no, _, _, price, _, _, _ in PRODUCTS:
            base = BASE_DEMAND[p_no]
            for w_cd, _, _, _, _ in WAREHOUSES:
                ww = WH_WEIGHT[w_cd]
                qty = int(base * mf * ww * random.uniform(0.85, 1.15))
                ret = int(qty * random.uniform(0.01, 0.04))  # 반품률 1~4%
                amt = qty * price

                rows.append({
                    "DEMAND_ID":   f"DMD{demand_id:05d}",
                    "YEAR_MONTH":  ym,
                    "PRODUCT_NO":  p_no,
                    "WAREHOUSE_CD": w_cd,
                    "DEMAND_QTY":  qty,
                    "SALES_AMT":   amt,
                    "RETURN_QTY":  ret,
                })
                demand_map[(p_no, w_cd, ym)] = qty
                demand_id += 1

    _write_csv("FACT_MONTHLY_DEMAND.csv", rows)
    print(f"  FACT_MONTHLY_DEMAND.csv — {len(rows)}행")
    return demand_map


# ── 5. FACT_INVENTORY_SNAPSHOT ────────────────────────────────────────────────
def write_fact_inventory_snapshot(demand_map):
    rows = []
    snap_id = 1
    # 제품→공급사 매핑
    prod_supplier = {p_no: sup_cd for p_no, _, _, _, _, _, sup_cd in PRODUCTS}
    prod_price    = {p_no: price  for p_no, _, _, price, _, _, _    in PRODUCTS}

    for snap_date in SNAPSHOTS:
        ym = snap_date[:7]  # "2024-10"
        for p_no, _, _, _, lead, _, _ in PRODUCTS:
            for w_cd, _, _, _, _ in WAREHOUSES:
                demand = demand_map.get((p_no, w_cd, ym), 0)
                # 안전재고 = 일평균수요 × (리드타임 + 7일 버퍼)
                daily_demand = demand / 30
                safety_stock = int(daily_demand * (lead + 7))
                # 재주문점 = 안전재고 + 리드타임 × 일평균수요
                reorder_point = int(safety_stock + daily_demand * lead)
                # 현재고 = 일정 범위 내 랜덤 (재주문점 기준 ±50%)
                stock_qty = int(reorder_point * random.uniform(0.5, 1.8))
                # 재고 상태
                if stock_qty <= 0:
                    status = "OUT_OF_STOCK"
                elif stock_qty < safety_stock:
                    status = "LOW_STOCK"
                elif stock_qty < reorder_point:
                    status = "REORDER_NEEDED"
                else:
                    status = "NORMAL"

                rows.append({
                    "SNAPSHOT_ID":       f"SNP{snap_id:05d}",
                    "SNAPSHOT_DATE":     snap_date,
                    "PRODUCT_NO":        p_no,
                    "SUPPLIER_CD":       prod_supplier[p_no],
                    "WAREHOUSE_CD":      w_cd,
                    "STOCK_QTY":         stock_qty,
                    "SAFETY_STOCK_QTY":  safety_stock,
                    "REORDER_POINT":     reorder_point,
                    "UNIT_COST":         int(prod_price[p_no] * 0.6),
                    "STATUS":            status,
                })
                snap_id += 1

    _write_csv("FACT_INVENTORY_SNAPSHOT.csv", rows)
    # 상태 분포 요약
    from collections import Counter
    dist = Counter(r["STATUS"] for r in rows)
    print(f"  FACT_INVENTORY_SNAPSHOT.csv — {len(rows)}행  |  상태분포: {dict(dist)}")
    return rows


# ── 6. SCHEMA_DEFINITION.json ─────────────────────────────────────────────────
def write_schema_json():
    schema = {
        "tables": [
            {
                "table_name":  "MST_PRODUCT",
                "table_type":  "master_table",
                "description": "상품 마스터 — 판매 상품의 기본 정보 및 조달 속성",
                "columns": [
                    {"name": "PRODUCT_NO",    "type": "VARCHAR(10)",  "pk": True,  "description": "상품 고유 번호 (PK)"},
                    {"name": "PRODUCT_NAME",  "type": "VARCHAR(100)", "pk": False, "description": "상품명"},
                    {"name": "CATEGORY_CD",   "type": "VARCHAR(20)",  "pk": False, "description": "카테고리 코드 (ELECTRONICS/ACCESSORIES)"},
                    {"name": "UNIT_PRICE",    "type": "INTEGER",      "pk": False, "description": "판매 단가 (원)"},
                    {"name": "LEAD_TIME_DAY", "type": "INTEGER",      "pk": False, "description": "조달 리드타임 (일)"},
                    {"name": "MIN_ORDER_QTY", "type": "INTEGER",      "pk": False, "description": "최소 발주 수량"},
                    {"name": "SUPPLIER_CD",   "type": "VARCHAR(10)",  "pk": False, "description": "주 공급사 코드 (FK → MST_SUPPLIER)"},
                ],
            },
            {
                "table_name":  "MST_SUPPLIER",
                "table_type":  "master_table",
                "description": "공급사 마스터 — 상품 공급업체의 기본 정보",
                "columns": [
                    {"name": "SUPPLIER_CD",       "type": "VARCHAR(10)",  "pk": True,  "description": "공급사 코드 (PK)"},
                    {"name": "SUPPLIER_NAME",     "type": "VARCHAR(100)", "pk": False, "description": "공급사명"},
                    {"name": "COUNTRY",           "type": "VARCHAR(20)",  "pk": False, "description": "공급사 소재 국가"},
                    {"name": "LEAD_TIME_DAY",     "type": "INTEGER",      "pk": False, "description": "평균 납기일 (일)"},
                    {"name": "RELIABILITY_SCORE", "type": "DECIMAL(3,1)", "pk": False, "description": "납기 신뢰도 점수 (0~5.0)"},
                    {"name": "CONTACT_EMAIL",     "type": "VARCHAR(100)", "pk": False, "description": "담당자 이메일"},
                ],
            },
            {
                "table_name":  "MST_WAREHOUSE",
                "table_type":  "master_table",
                "description": "창고 마스터 — 물류 거점(창고) 정보",
                "columns": [
                    {"name": "WAREHOUSE_CD",   "type": "VARCHAR(10)",  "pk": True,  "description": "창고 코드 (PK)"},
                    {"name": "WAREHOUSE_NAME", "type": "VARCHAR(100)", "pk": False, "description": "창고명"},
                    {"name": "LOCATION",       "type": "VARCHAR(100)", "pk": False, "description": "창고 소재지"},
                    {"name": "CAPACITY",       "type": "INTEGER",      "pk": False, "description": "총 보관 가능 수량"},
                    {"name": "REGION",         "type": "VARCHAR(20)",  "pk": False, "description": "권역 (수도권/영남/충청)"},
                ],
            },
            {
                "table_name":  "FACT_MONTHLY_DEMAND",
                "table_type":  "fact_table",
                "description": "월별 수요 실적 — 상품×창고별 월 판매량·반품량·매출",
                "columns": [
                    {"name": "DEMAND_ID",    "type": "VARCHAR(10)",  "pk": True,  "description": "수요 레코드 ID (PK)"},
                    {"name": "YEAR_MONTH",   "type": "VARCHAR(7)",   "pk": False, "description": "집계 연월 (YYYY-MM)"},
                    {"name": "PRODUCT_NO",   "type": "VARCHAR(10)",  "pk": False, "description": "상품 번호 (FK → MST_PRODUCT)"},
                    {"name": "WAREHOUSE_CD", "type": "VARCHAR(10)",  "pk": False, "description": "창고 코드 (FK → MST_WAREHOUSE)"},
                    {"name": "DEMAND_QTY",   "type": "INTEGER",      "pk": False, "description": "판매 수량"},
                    {"name": "SALES_AMT",    "type": "BIGINT",       "pk": False, "description": "매출 금액 (원)"},
                    {"name": "RETURN_QTY",   "type": "INTEGER",      "pk": False, "description": "반품 수량"},
                ],
            },
            {
                "table_name":  "FACT_INVENTORY_SNAPSHOT",
                "table_type":  "fact_table",
                "description": "재고 스냅샷 — 특정 시점의 상품×창고별 재고 현황",
                "columns": [
                    {"name": "SNAPSHOT_ID",      "type": "VARCHAR(10)",  "pk": True,  "description": "스냅샷 ID (PK)"},
                    {"name": "SNAPSHOT_DATE",    "type": "DATE",         "pk": False, "description": "스냅샷 기준일"},
                    {"name": "PRODUCT_NO",       "type": "VARCHAR(10)",  "pk": False, "description": "상품 번호 (FK → MST_PRODUCT)"},
                    {"name": "SUPPLIER_CD",      "type": "VARCHAR(10)",  "pk": False, "description": "공급사 코드 (FK → MST_SUPPLIER)"},
                    {"name": "WAREHOUSE_CD",     "type": "VARCHAR(10)",  "pk": False, "description": "창고 코드 (FK → MST_WAREHOUSE)"},
                    {"name": "STOCK_QTY",        "type": "INTEGER",      "pk": False, "description": "현재고 수량"},
                    {"name": "SAFETY_STOCK_QTY", "type": "INTEGER",      "pk": False, "description": "안전재고 수량"},
                    {"name": "REORDER_POINT",    "type": "INTEGER",      "pk": False, "description": "재주문점 수량"},
                    {"name": "UNIT_COST",        "type": "INTEGER",      "pk": False, "description": "상품 단가 (원가 기준)"},
                    {"name": "STATUS",           "type": "VARCHAR(20)",  "pk": False, "description": "재고 상태 (NORMAL/REORDER_NEEDED/LOW_STOCK/OUT_OF_STOCK)"},
                ],
            },
        ],
        "relationships": [
            {"from": "MST_PRODUCT",            "to": "MST_SUPPLIER",   "join_key": "SUPPLIER_CD",   "relation": "N:1"},
            {"from": "FACT_MONTHLY_DEMAND",    "to": "MST_PRODUCT",    "join_key": "PRODUCT_NO",    "relation": "N:1"},
            {"from": "FACT_MONTHLY_DEMAND",    "to": "MST_WAREHOUSE",  "join_key": "WAREHOUSE_CD",  "relation": "N:1"},
            {"from": "FACT_INVENTORY_SNAPSHOT","to": "MST_PRODUCT",    "join_key": "PRODUCT_NO",    "relation": "N:1"},
            {"from": "FACT_INVENTORY_SNAPSHOT","to": "MST_SUPPLIER",   "join_key": "SUPPLIER_CD",   "relation": "N:1"},
            {"from": "FACT_INVENTORY_SNAPSHOT","to": "MST_WAREHOUSE",  "join_key": "WAREHOUSE_CD",  "relation": "N:1"},
        ],
    }
    path = os.path.join(OUT, "SCHEMA_DEFINITION.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    print(f"  SCHEMA_DEFINITION.json — 테이블 {len(schema['tables'])}개, 관계 {len(schema['relationships'])}개")


# ── 7. LOGIC_DOCUMENT.txt ─────────────────────────────────────────────────────
def write_logic_document():
    doc = """\
================================================================================
이커머스 재고관리 도메인 — 데이터 구조 및 비즈니스 로직 설명서
================================================================================

1. 테이블 구조 개요
--------------------------------------------------------------------------------

[MST_PRODUCT] 상품 마스터
  - PRODUCT_NO     : 상품 고유 번호 (PK). 모든 팩트 테이블의 기준 키.
  - PRODUCT_NAME   : 상품명.
  - CATEGORY_CD    : 카테고리 코드. 현재 ELECTRONICS, ACCESSORIES 두 가지.
  - UNIT_PRICE     : 소비자 판매 단가 (원). FACT_INVENTORY_SNAPSHOT.UNIT_COST와
                     구분됨 — UNIT_PRICE는 판매가, UNIT_COST는 원가(판매가×0.6).
  - LEAD_TIME_DAY  : 공급사로부터 입고까지 소요 일수.
                     안전재고 및 재주문점 계산에 직접 사용됨.
  - MIN_ORDER_QTY  : 공급사에 발주 가능한 최소 수량.
  - SUPPLIER_CD    : 주 공급사 코드 (FK → MST_SUPPLIER.SUPPLIER_CD).

[MST_SUPPLIER] 공급사 마스터
  - SUPPLIER_CD        : 공급사 고유 코드 (PK).
  - SUPPLIER_NAME      : 공급사명.
  - COUNTRY            : 소재 국가. 한국 공급사(SUP001, SUP003)는 리드타임이 짧고
                         신뢰도 점수가 높음. 중국 공급사(SUP002)는 리드타임 21일.
  - LEAD_TIME_DAY      : 공급사 측 평균 납기. MST_PRODUCT.LEAD_TIME_DAY와 독립적으로
                         관리되며, 실제 납기 예측 시 두 값을 비교 검토함.
  - RELIABILITY_SCORE  : 납기 준수율 기반 신뢰도 점수 (0~5.0).

[MST_WAREHOUSE] 창고 마스터
  - WAREHOUSE_CD   : 창고 코드 (PK). WH001(서울), WH002(부산), WH003(대전).
  - WAREHOUSE_NAME : 창고명.
  - LOCATION       : 물리적 소재지.
  - CAPACITY       : 총 보관 가능 수량.
  - REGION         : 권역 구분. 수요 배분 및 권역별 재고 분석에 활용.

[FACT_MONTHLY_DEMAND] 월별 수요 실적 팩트
  - DEMAND_ID    : 레코드 고유 ID (PK). DMD + 5자리 순번.
  - YEAR_MONTH   : 집계 연월 (YYYY-MM 형식). 2024-10 ~ 2024-12 데이터 포함.
  - PRODUCT_NO   : 상품 번호 (FK → MST_PRODUCT.PRODUCT_NO).
  - WAREHOUSE_CD : 창고 코드 (FK → MST_WAREHOUSE.WAREHOUSE_CD).
  - DEMAND_QTY   : 해당 월 판매 수량.
  - SALES_AMT    : 매출 금액 = DEMAND_QTY × MST_PRODUCT.UNIT_PRICE.
  - RETURN_QTY   : 반품 수량 (DEMAND_QTY의 1~4% 수준).

  ※ 수요 패턴
    - 수도권(WH001) 수요 가중치 = 1.0 (기준)
    - 영남(WH002) 수요 가중치   = 0.6
    - 충청(WH003) 수요 가중치   = 0.4
    - 연말 성수기 계수: 10월=1.0배, 11월=1.3배, 12월=1.7배

[FACT_INVENTORY_SNAPSHOT] 재고 스냅샷 팩트
  - SNAPSHOT_ID      : 스냅샷 ID (PK). SNP + 5자리 순번.
  - SNAPSHOT_DATE    : 스냅샷 기준일. 월말 기준 (10-31, 11-30, 12-31).
  - PRODUCT_NO       : 상품 번호 (FK → MST_PRODUCT.PRODUCT_NO).
  - SUPPLIER_CD      : 공급사 코드 (FK → MST_SUPPLIER.SUPPLIER_CD).
                       MST_PRODUCT.SUPPLIER_CD와 동일한 공급사를 참조.
  - WAREHOUSE_CD     : 창고 코드 (FK → MST_WAREHOUSE.WAREHOUSE_CD).
  - STOCK_QTY        : 해당 시점 현재고 수량.
  - SAFETY_STOCK_QTY : 안전재고 수량.
  - REORDER_POINT    : 재주문점 수량.
  - UNIT_COST        : 원가 (= MST_PRODUCT.UNIT_PRICE × 0.6).
  - STATUS           : 재고 상태 코드 (아래 계산 로직 참조).

2. 핵심 계산 로직
--------------------------------------------------------------------------------

[안전재고 계산]
  일평균수요     = FACT_MONTHLY_DEMAND.DEMAND_QTY ÷ 30
  SAFETY_STOCK_QTY = 일평균수요 × (MST_PRODUCT.LEAD_TIME_DAY + 7일 버퍼)

  예시: P001(무선 이어폰 프로), WH001, 2024-10
    DEMAND_QTY   = 약 320개 → 일평균수요 ≈ 10.7개/일
    LEAD_TIME_DAY = 14일 (공급사 SUP002 기준)
    SAFETY_STOCK  = 10.7 × (14 + 7) ≈ 224개

[재주문점 계산]
  REORDER_POINT = SAFETY_STOCK_QTY + 일평균수요 × MST_PRODUCT.LEAD_TIME_DAY

  예시: P001, WH001
    REORDER_POINT = 224 + 10.7 × 14 ≈ 374개

[재고 상태 분류 — FACT_INVENTORY_SNAPSHOT.STATUS]
  STOCK_QTY <= 0                           → OUT_OF_STOCK (긴급 발주 필요)
  0 < STOCK_QTY < SAFETY_STOCK_QTY        → LOW_STOCK (안전재고 미달)
  SAFETY_STOCK_QTY <= STOCK_QTY
                    < REORDER_POINT        → REORDER_NEEDED (발주 검토 필요)
  STOCK_QTY >= REORDER_POINT              → NORMAL (적정 재고)

3. 테이블 간 JOIN 관계
--------------------------------------------------------------------------------

[주요 분석 JOIN 패턴]

  ① 상품별 공급사 리드타임 비교
     MST_PRODUCT
       JOIN MST_SUPPLIER ON MST_PRODUCT.SUPPLIER_CD = MST_SUPPLIER.SUPPLIER_CD
     → MST_PRODUCT.LEAD_TIME_DAY vs MST_SUPPLIER.LEAD_TIME_DAY 비교 분석

  ② 월별 수요 + 상품 정보 결합
     FACT_MONTHLY_DEMAND
       JOIN MST_PRODUCT   ON FACT_MONTHLY_DEMAND.PRODUCT_NO   = MST_PRODUCT.PRODUCT_NO
       JOIN MST_WAREHOUSE ON FACT_MONTHLY_DEMAND.WAREHOUSE_CD = MST_WAREHOUSE.WAREHOUSE_CD
     → 권역별·카테고리별 수요 추이 분석

  ③ 재고 상태 + 공급사 신뢰도 결합 (발주 의사결정)
     FACT_INVENTORY_SNAPSHOT
       JOIN MST_PRODUCT   ON FACT_INVENTORY_SNAPSHOT.PRODUCT_NO   = MST_PRODUCT.PRODUCT_NO
       JOIN MST_SUPPLIER  ON FACT_INVENTORY_SNAPSHOT.SUPPLIER_CD  = MST_SUPPLIER.SUPPLIER_CD
       JOIN MST_WAREHOUSE ON FACT_INVENTORY_SNAPSHOT.WAREHOUSE_CD = MST_WAREHOUSE.WAREHOUSE_CD
     → STATUS = 'REORDER_NEEDED' OR 'LOW_STOCK' 인 레코드 필터링
       → MST_SUPPLIER.RELIABILITY_SCORE 낮은 공급사 우선 관리 대상

  ④ 수요 대비 재고 커버리지 계산
     FACT_INVENTORY_SNAPSHOT.STOCK_QTY
       ÷ (FACT_MONTHLY_DEMAND.DEMAND_QTY ÷ 30)
     = 현재고로 몇 일치 수요를 감당할 수 있는지 (재고 커버리지, 일)
     JOIN 키: PRODUCT_NO, WAREHOUSE_CD, YEAR_MONTH(= SNAPSHOT_DATE의 연월)

4. 공통 키 (FK 연결 구조)
--------------------------------------------------------------------------------

  PRODUCT_NO   : MST_PRODUCT(PK) ← FACT_MONTHLY_DEMAND, FACT_INVENTORY_SNAPSHOT
  SUPPLIER_CD  : MST_SUPPLIER(PK) ← MST_PRODUCT, FACT_INVENTORY_SNAPSHOT
  WAREHOUSE_CD : MST_WAREHOUSE(PK) ← FACT_MONTHLY_DEMAND, FACT_INVENTORY_SNAPSHOT

  [참조 무결성]
    - FACT_MONTHLY_DEMAND의 모든 PRODUCT_NO 값은 MST_PRODUCT에 존재
    - FACT_MONTHLY_DEMAND의 모든 WAREHOUSE_CD 값은 MST_WAREHOUSE에 존재
    - FACT_INVENTORY_SNAPSHOT의 모든 PRODUCT_NO / SUPPLIER_CD / WAREHOUSE_CD 값은
      각각 MST_PRODUCT / MST_SUPPLIER / MST_WAREHOUSE에 존재
    - FACT_INVENTORY_SNAPSHOT.SUPPLIER_CD = 해당 PRODUCT_NO의 MST_PRODUCT.SUPPLIER_CD
      (동일 공급사 참조 보장)

5. 데이터 범위 및 특이사항
--------------------------------------------------------------------------------

  기간       : 2024년 10월 ~ 12월 (3개월)
  상품 수    : 8개 (ELECTRONICS 6개, ACCESSORIES 2개)
  공급사 수  : 3개 (국내 2개, 해외 1개)
  창고 수    : 3개 (수도권·영남·충청 각 1개)
  수요 레코드: 72개 (8 상품 × 3 창고 × 3 개월)
  스냅샷 레코드: 72개 (8 상품 × 3 창고 × 3 월말 시점)

  [주의사항]
    - FACT_MONTHLY_DEMAND.DEMAND_QTY는 판매 완료 수량으로, 반품 전 gross 수량임
    - 실제 순수요 = DEMAND_QTY - RETURN_QTY
    - FACT_INVENTORY_SNAPSHOT의 STOCK_QTY는 해당 월말 기준 장부 재고로,
      실사 재고(physical count)와 차이가 있을 수 있음
    - 연말 성수기(12월)에 DEMAND_QTY가 높아 LOW_STOCK / REORDER_NEEDED 상태
      비율이 증가하는 패턴이 데이터에 반영되어 있음

================================================================================
"""
    path = os.path.join(OUT, "LOGIC_DOCUMENT.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"  LOGIC_DOCUMENT.txt — {len(doc.splitlines())}줄")


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────
def _write_csv(filename: str, rows: list):
    if not rows:
        return
    path = os.path.join(OUT, filename)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# ── 실행 ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n데모 데이터 생성 시작 → {OUT}/\n")
    write_mst_product()
    write_mst_supplier()
    write_mst_warehouse()
    demand_map = write_fact_monthly_demand()
    snap_rows  = write_fact_inventory_snapshot(demand_map)
    write_schema_json()
    write_logic_document()

    # 참조 무결성 검증
    print("\n[참조 무결성 검증]")
    import csv as _csv

    def load_csv(fname):
        with open(os.path.join(OUT, fname), encoding="utf-8-sig") as f:
            return list(_csv.DictReader(f))

    p_keys  = {r["PRODUCT_NO"]   for r in load_csv("MST_PRODUCT.csv")}
    s_keys  = {r["SUPPLIER_CD"]  for r in load_csv("MST_SUPPLIER.csv")}
    w_keys  = {r["WAREHOUSE_CD"] for r in load_csv("MST_WAREHOUSE.csv")}

    demand_rows = load_csv("FACT_MONTHLY_DEMAND.csv")
    inv_rows    = load_csv("FACT_INVENTORY_SNAPSHOT.csv")

    checks = [
        ("FACT_MONTHLY_DEMAND.PRODUCT_NO    → MST_PRODUCT",
         all(r["PRODUCT_NO"]   in p_keys for r in demand_rows)),
        ("FACT_MONTHLY_DEMAND.WAREHOUSE_CD  → MST_WAREHOUSE",
         all(r["WAREHOUSE_CD"] in w_keys for r in demand_rows)),
        ("FACT_INVENTORY_SNAPSHOT.PRODUCT_NO   → MST_PRODUCT",
         all(r["PRODUCT_NO"]   in p_keys for r in inv_rows)),
        ("FACT_INVENTORY_SNAPSHOT.SUPPLIER_CD  → MST_SUPPLIER",
         all(r["SUPPLIER_CD"]  in s_keys for r in inv_rows)),
        ("FACT_INVENTORY_SNAPSHOT.WAREHOUSE_CD → MST_WAREHOUSE",
         all(r["WAREHOUSE_CD"] in w_keys for r in inv_rows)),
    ]

    all_ok = True
    for label, ok in checks:
        status = "[PASS]" if ok else "[FAIL]"
        print(f"  {status}  {label}")
        all_ok &= ok

    print(f"\n{'모든 참조 무결성 검증 통과!' if all_ok else '일부 검증 실패 — 위 항목 확인 필요'}")
    print(f"\n생성 완료: {OUT}/\n")
