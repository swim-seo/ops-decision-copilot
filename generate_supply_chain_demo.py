"""
바닐라코 글로벌 공급망 · 리드타임 기반 재고 최적화 데이터셋 생성기

추가 테이블:
  - MST_OFFICE               : 지점/창고별 LT·T·SS_PARAM 재고정책 파라미터
  - MST_PART                 : 부품(완제품·원료·용기) 마스터
  - MST_SUPPLY_ROUTE         : 공급업체 → 지점 운송 루트별 리드타임·비용
  - FACT_REPLENISHMENT_ORDER : 3년치 발주 이력 (2022-01 ~ 2024-12)
  - FACT_STOCKOUT_EVENT      : 품절 발생 이력
  - DATA_DICTIONARY.csv      : 전체 테이블·컬럼 설명서
"""

import csv
import os
import random
from datetime import date, timedelta

random.seed(7)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# 1. MST_OFFICE  — 지점/창고별 재고정책 파라미터
#    LT  : Lead Time (일) — 발주 후 납품까지 소요일 (지점마다 다름)
#    T   : Review Period (일) — 정기 발주 검토 주기 (지점마다 다름)
#    SS_PARAM : 안전재고 계수 — z-score (95% 서비스 수준 = 1.65 고정)
#    SS 계산식: SS = SS_PARAM × σ_demand × √(LT + T)
# ═══════════════════════════════════════════════════════════════

OFFICES = [
    # OFFICE_CD, OFFICE_NAME,          REGION, OFFICE_TYPE, LT, T,  SS_PARAM, CURRENCY, TIMEZONE
    ("KR-ICN", "인천 물류센터(메인)",   "KR",   "창고",      7,  14, 1.65,    "KRW", "Asia/Seoul"),
    ("KR-MDG", "명동 직영매장",         "KR",   "매장",      2,   7, 1.65,    "KRW", "Asia/Seoul"),
    ("KR-SSU", "성수 직영매장",         "KR",   "매장",      2,   7, 1.65,    "KRW", "Asia/Seoul"),
    ("US-LAX", "LA 물류센터",           "US",   "창고",     21,  30, 1.65,    "USD", "America/Los_Angeles"),
    ("SEA-SGP","싱가포르 허브",         "SEA",  "창고",     14,  21, 1.65,    "USD", "Asia/Singapore"),
    ("SEA-JKT","자카르타 거점창고",     "SEA",  "창고",     18,  28, 1.65,    "USD", "Asia/Jakarta"),
    ("SEA-BKK","방콕 거점창고",         "SEA",  "창고",     16,  21, 1.65,    "USD", "Asia/Bangkok"),
]

OFFICE_FIELDS = ["OFFICE_CD","OFFICE_NAME","REGION","OFFICE_TYPE","LT","T","SS_PARAM","CURRENCY","TIMEZONE"]


# ═══════════════════════════════════════════════════════════════
# 2. MST_PART  — 부품(완제품/원료/용기) 마스터
#    PART_CD   : 부품코드  FG=완제품 RM=원료 PK=용기
#    LINKED_PRODUCT_ID : MST_PRODUCT FK (완제품만)
# ═══════════════════════════════════════════════════════════════

PARTS = [
    # PART_CD, PART_NAME,                     PART_TYPE, LINKED_PRODUCT_ID, UNIT, UNIT_COST_KRW, STD_DEMAND_MONTHLY
    ("FG-001","클린잇제로 클렌징밤 50ml",      "완제품",  "PRD001",  "EA",  22000,  800),
    ("FG-002","선프로텍터 선크림 SPF50+ 50ml", "완제품",  "PRD002",  "EA",  18000,  950),
    ("FG-003","인텐시브 수분크림 50ml",        "완제품",  "PRD003",  "EA",  32000,  600),
    ("FG-004","퍼스트 토너 150ml",             "완제품",  "PRD004",  "EA",  25000,  700),
    ("FG-005","앰플 에센스 30ml",              "완제품",  "PRD005",  "EA",  45000,  400),
    ("FG-006","레티놀 리뉴얼 세럼 30ml",      "완제품",  "PRD006",  "EA",  55000,  300),
    ("FG-007","벨벳 립틴트 4g",               "완제품",  "PRD008",  "EA",  12000, 1200),
    ("FG-008","퍼펙트 커버 쿠션 15g",         "완제품",  "PRD016",  "EA",  28000,  500),
    ("FG-009","선쿠션 SPF50+ 15g",            "완제품",  "PRD020",  "EA",  24000,  700),
    ("FG-010","볼루밍 마스카라 8ml",           "완제품",  "PRD012",  "EA",  16000,  650),
    ("RM-001","히알루론산 원료",               "원료",    None,      "KG",   8500,   45),
    ("RM-002","레티놀 원료 0.1%",             "원료",    None,      "KG", 120000,    8),
    ("RM-003","자외선 차단 필터(옥시벤존)",   "원료",    None,      "KG",  35000,   30),
    ("PK-001","펌프 용기 50ml (스킨케어)",    "용기",    None,      "EA",   1200, 2000),
    ("PK-002","쿠션 케이스 (베이스)",         "용기",    None,      "EA",   2500,  800),
]

PART_FIELDS = ["PART_CD","PART_NAME","PART_TYPE","LINKED_PRODUCT_ID","UNIT","UNIT_COST_KRW","STD_DEMAND_MONTHLY"]


# ═══════════════════════════════════════════════════════════════
# 3. MST_SUPPLY_ROUTE  — 공급업체 → 지점 운송 루트
#    ROUTE_LT_DAYS  : 이 루트 실제 리드타임 (MST_OFFICE.LT의 근거)
#    RELIABILITY_PCT: 납기 준수율 (%)
# ═══════════════════════════════════════════════════════════════

ROUTES = [
    # ROUTE_ID, SUPPLIER_ID, OFFICE_CD,  TRANSPORT_MODE, ROUTE_LT_DAYS, FREIGHT_COST_KRW, RELIABILITY_PCT
    ("RT001","SUP001","KR-ICN","육운",     5, 150000, 97),
    ("RT002","SUP004","KR-ICN","육운",     7, 200000, 95),
    ("RT003","SUP001","KR-MDG","육운",     2,  50000, 99),
    ("RT004","SUP001","KR-SSU","육운",     2,  50000, 99),
    ("RT005","SUP003","US-LAX","해운",    21, 850000, 88),
    ("RT006","SUP007","US-LAX","해운",    25, 920000, 85),
    ("RT007","SUP003","SEA-SGP","해운",   14, 620000, 90),
    ("RT008","SUP007","SEA-SGP","해운",   18, 700000, 87),
    ("RT009","SUP003","SEA-JKT","해운",   18, 680000, 86),
    ("RT010","SUP008","SEA-JKT","항공",    5, 1800000, 96),
    ("RT011","SUP007","SEA-BKK","해운",   16, 650000, 88),
    ("RT012","SUP010","KR-ICN","항공",     3, 2100000, 98),
]

ROUTE_FIELDS = ["ROUTE_ID","SUPPLIER_ID","OFFICE_CD","TRANSPORT_MODE","ROUTE_LT_DAYS","FREIGHT_COST_KRW","RELIABILITY_PCT"]


# ═══════════════════════════════════════════════════════════════
# 4. FACT_REPLENISHMENT_ORDER  — 3년치 발주 이력
#    기간: 2022-01 ~ 2024-12 (36개월)
#    ORDER_YM   : 발주년월 (YYYYMM)
#    ORDER_DT   : 발주일   (YYYYMMDD)
#    PROMISED_DT: 납품예정일 (YYYYMMDD) = ORDER_DT + LT
#    ACTUAL_DT  : 실납품일  (YYYYMMDD) = PROMISED_DT + 지연일수
# ═══════════════════════════════════════════════════════════════

office_lt = {r[0]: r[4] for r in OFFICES}   # OFFICE_CD → LT
office_t  = {r[0]: r[5] for r in OFFICES}   # OFFICE_CD → T
part_demand = {r[0]: r[6] for r in PARTS}   # PART_CD → STD_DEMAND_MONTHLY
part_cost   = {r[0]: r[5] for r in PARTS}   # PART_CD → UNIT_COST_KRW

# 지점별 취급 부품 (현실적 매핑)
OFFICE_PART_MAP = {
    "KR-ICN": [p[0] for p in PARTS],                                   # 전체
    "KR-MDG": ["FG-001","FG-002","FG-003","FG-004","FG-007","FG-008","FG-009","FG-010"],
    "KR-SSU": ["FG-001","FG-002","FG-003","FG-004","FG-007","FG-008","FG-009","FG-010"],
    "US-LAX": ["FG-001","FG-002","FG-003","FG-005","FG-006","FG-008","FG-009","RM-003"],
    "SEA-SGP":["FG-002","FG-003","FG-004","FG-007","FG-009","PK-001","PK-002"],
    "SEA-JKT":["FG-002","FG-007","FG-009","FG-010","PK-001"],
    "SEA-BKK":["FG-002","FG-003","FG-007","FG-009","PK-002"],
}

# 납기 지연 시뮬레이션: 지점별 평균 지연일
DELAY_PROFILE = {
    "KR-ICN": (0, 2),    # 평균 0일, 최대 2일 지연 (국내)
    "KR-MDG": (0, 1),
    "KR-SSU": (0, 1),
    "US-LAX": (3, 10),   # 평균 3일, 최대 10일 (해운 리스크)
    "SEA-SGP":(2, 8),
    "SEA-JKT":(3, 12),
    "SEA-BKK":(2, 9),
}

def random_delay(office_cd: str) -> int:
    """지점별 지연일 랜덤 생성 (정규분포 근사)"""
    avg, mx = DELAY_PROFILE[office_cd]
    d = int(random.gauss(avg, mx / 3))
    return max(-2, min(d, mx))   # -2(조기납품)~mx 범위

def workday(base: date, days: int) -> date:
    return base + timedelta(days=days)

order_rows = []
order_id = 1

for year in range(2022, 2025):          # 2022~2024
    for month in range(1, 13):
        ym = f"{year}{month:02d}"
        month_start = date(year, month, 1)
        # 월말 계산
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)
        month_days = (month_end - month_start).days + 1

        for ofc_cd, parts in OFFICE_PART_MAP.items():
            lt = office_lt[ofc_cd]
            t  = office_t[ofc_cd]

            for part_cd in parts:
                # T일마다 발주 → 한 달 내 발주 횟수
                orders_in_month = max(1, round(month_days / t))

                for i in range(orders_in_month):
                    # 발주일: 월 내 균등 분산
                    day_offset = int((i + 0.5) * month_days / orders_in_month)
                    day_offset = min(day_offset, month_days - 1)
                    order_dt = month_start + timedelta(days=day_offset)

                    promised_dt = workday(order_dt, lt)
                    delay = random_delay(ofc_cd)
                    actual_dt = workday(promised_dt, delay)

                    base_demand = part_demand[part_cd]
                    # 주문량: 평균 수요 기반 (T일치 + 약간 노이즈)
                    qty = max(10, int(base_demand * (t / 30) * random.uniform(0.85, 1.20)))

                    # 수령량: 가끔 부분 수령
                    if random.random() < 0.05:   # 5% 확률 부분 수령
                        rcv_qty = int(qty * random.uniform(0.70, 0.90))
                        status = "PARTIAL"
                    elif actual_dt > promised_dt + timedelta(days=3):
                        rcv_qty = qty
                        status = "DELAYED"
                    elif actual_dt.year > 2024 or (actual_dt.year == 2024 and actual_dt.month == 12 and actual_dt.day > 31):
                        rcv_qty = 0
                        status = "PENDING"
                    else:
                        rcv_qty = qty
                        status = "DELIVERED"

                    cost = part_cost[part_cd]
                    currency = "KRW" if ofc_cd.startswith("KR") else "USD"
                    amount = qty * cost if currency == "KRW" else round(qty * cost / 1300, 2)

                    order_rows.append({
                        "ORDER_ID":      f"PO{order_id:07d}",
                        "OFFICE_CD":     ofc_cd,
                        "PART_CD":       part_cd,
                        "ORDER_YM":      ym,
                        "ORDER_DT":      order_dt.strftime("%Y%m%d"),
                        "PROMISED_DT":   promised_dt.strftime("%Y%m%d"),
                        "ACTUAL_DT":     actual_dt.strftime("%Y%m%d") if status != "PENDING" else "",
                        "ORDER_QTY":     qty,
                        "RECEIVED_QTY":  rcv_qty,
                        "UNIT_COST":     cost,
                        "CURRENCY":      currency,
                        "ORDER_AMOUNT":  amount,
                        "DELAY_DAYS":    max(0, delay),
                        "STATUS":        status,
                    })
                    order_id += 1

ORDER_FIELDS = list(order_rows[0].keys())


# ═══════════════════════════════════════════════════════════════
# 5. FACT_STOCKOUT_EVENT  — 품절 발생 이력
# ═══════════════════════════════════════════════════════════════

CAUSE_CODES = ["LATE_DELIVERY","DEMAND_SURGE","FORECAST_ERROR","SUPPLIER_ISSUE","PORT_DELAY"]

stockout_rows = []
sout_id = 1

# 지연 발주에서 품절 이벤트 도출 (DELAYED/PARTIAL 건 중 일부)
delayed = [r for r in order_rows if r["STATUS"] in ("DELAYED", "PARTIAL")]
for r in random.sample(delayed, min(len(delayed), 120)):
    start_dt = date.fromisoformat(
        r["PROMISED_DT"][:4] + "-" + r["PROMISED_DT"][4:6] + "-" + r["PROMISED_DT"][6:]
    )
    duration = random.randint(1, r["DELAY_DAYS"] if r["DELAY_DAYS"] > 0 else 3)
    end_dt = start_dt + timedelta(days=duration)
    base_d = part_demand.get(r["PART_CD"], 100)
    lost = int(base_d / 30 * duration * random.uniform(0.5, 1.2))

    stockout_rows.append({
        "STOCKOUT_ID":    f"SO{sout_id:05d}",
        "OFFICE_CD":      r["OFFICE_CD"],
        "PART_CD":        r["PART_CD"],
        "STOCKOUT_YM":    r["ORDER_YM"],
        "START_DT":       start_dt.strftime("%Y%m%d"),
        "END_DT":         end_dt.strftime("%Y%m%d"),
        "DURATION_DAYS":  duration,
        "LOST_SALES_QTY": max(0, lost),
        "CAUSE_CODE":     random.choice(CAUSE_CODES),
        "LINKED_ORDER_ID":r["ORDER_ID"],
    })
    sout_id += 1

STOCKOUT_FIELDS = list(stockout_rows[0].keys())


# ═══════════════════════════════════════════════════════════════
# 6. DATA_DICTIONARY.csv  — 전체 테이블·컬럼 설명서
# ═══════════════════════════════════════════════════════════════

DD_FIELDS = ["TABLE_NAME","COLUMN_NAME","COLUMN_NAME_KO","DATA_TYPE","NULLABLE","IS_PK","IS_FK","FK_REF","DESCRIPTION"]

DATA_DICT = [
    # ── MST_OFFICE ──
    ("MST_OFFICE","OFFICE_CD",    "지점코드",        "VARCHAR(8)", "N","Y","N","","지점/창고 고유 코드 (예: KR-ICN, US-LAX)"),
    ("MST_OFFICE","OFFICE_NAME",  "지점명",          "VARCHAR(30)","N","N","N","","지점 또는 창고의 공식 명칭"),
    ("MST_OFFICE","REGION",       "지역",            "CHAR(3)",    "N","N","N","","운영 지역 코드 (KR/US/SEA)"),
    ("MST_OFFICE","OFFICE_TYPE",  "지점유형",        "VARCHAR(5)", "N","N","N","","창고 또는 매장 구분"),
    ("MST_OFFICE","LT",           "리드타임(일)",    "INTEGER",    "N","N","N","","발주 후 납품까지 소요 기간(일). 지점별 상이"),
    ("MST_OFFICE","T",            "발주주기(일)",    "INTEGER",    "N","N","N","","정기 발주 검토 주기(일). 지점별 상이"),
    ("MST_OFFICE","SS_PARAM",     "안전재고계수",    "DECIMAL(4,2)","N","N","N","","안전재고 계산용 z-score. 95% 서비스 수준=1.65 (전 지점 고정)"),
    ("MST_OFFICE","CURRENCY",     "통화",            "CHAR(3)",    "N","N","N","","해당 지점의 거래 통화 (KRW/USD)"),
    ("MST_OFFICE","TIMEZONE",     "타임존",          "VARCHAR(30)","N","N","N","","지점 현지 타임존"),
    # ── MST_PART ──
    ("MST_PART","PART_CD",            "부품코드",        "VARCHAR(6)", "N","Y","N","","부품 고유 코드 (FG=완제품, RM=원료, PK=용기)"),
    ("MST_PART","PART_NAME",          "부품명",          "VARCHAR(60)","N","N","N","","부품 또는 원료의 공식 명칭"),
    ("MST_PART","PART_TYPE",          "부품유형",        "VARCHAR(5)", "N","N","N","","완제품/원료/용기 구분"),
    ("MST_PART","LINKED_PRODUCT_ID",  "연결상품ID",      "VARCHAR(6)", "Y","N","Y","MST_PRODUCT.PRODUCT_ID","완제품의 경우 MST_PRODUCT와 연결 (원료·용기는 NULL)"),
    ("MST_PART","UNIT",               "단위",            "VARCHAR(5)", "N","N","N","","수량 단위 (EA=개, KG=킬로그램)"),
    ("MST_PART","UNIT_COST_KRW",      "단가(원)",        "INTEGER",    "N","N","N","","부품 단가 (KRW 기준)"),
    ("MST_PART","STD_DEMAND_MONTHLY", "월표준수요",      "INTEGER",    "N","N","N","","전사 기준 월평균 수요량 (SS 초기값 산출용)"),
    # ── MST_SUPPLY_ROUTE ──
    ("MST_SUPPLY_ROUTE","ROUTE_ID",         "루트ID",         "VARCHAR(5)", "N","Y","N","","공급 루트 고유 ID"),
    ("MST_SUPPLY_ROUTE","SUPPLIER_ID",      "공급업체코드",   "VARCHAR(6)", "N","N","Y","MST_SUPPLIER.SUPPLIER_ID","공급업체 FK"),
    ("MST_SUPPLY_ROUTE","OFFICE_CD",        "지점코드",       "VARCHAR(8)", "N","N","Y","MST_OFFICE.OFFICE_CD","도착 지점 FK"),
    ("MST_SUPPLY_ROUTE","TRANSPORT_MODE",   "운송수단",       "VARCHAR(5)", "N","N","N","","운송 방식 (육운/해운/항공)"),
    ("MST_SUPPLY_ROUTE","ROUTE_LT_DAYS",    "루트리드타임",   "INTEGER",    "N","N","N","","이 루트의 실제 리드타임(일). MST_OFFICE.LT의 산출 근거"),
    ("MST_SUPPLY_ROUTE","FREIGHT_COST_KRW", "운임(원)",       "INTEGER",    "N","N","N","","발주 1건당 운임 (KRW)"),
    ("MST_SUPPLY_ROUTE","RELIABILITY_PCT",  "납기준수율(%)",  "INTEGER",    "N","N","N","","과거 실적 기반 납기 준수율 (%)"),
    # ── FACT_REPLENISHMENT_ORDER ──
    ("FACT_REPLENISHMENT_ORDER","ORDER_ID",      "발주ID",       "VARCHAR(9)", "N","Y","N","","발주 고유 ID (PO 일련번호)"),
    ("FACT_REPLENISHMENT_ORDER","OFFICE_CD",     "지점코드",     "VARCHAR(8)", "N","N","Y","MST_OFFICE.OFFICE_CD","수령 지점 FK"),
    ("FACT_REPLENISHMENT_ORDER","PART_CD",       "부품코드",     "VARCHAR(6)", "N","N","Y","MST_PART.PART_CD","발주 부품 FK"),
    ("FACT_REPLENISHMENT_ORDER","ORDER_YM",      "발주년월",     "CHAR(6)",    "N","N","N","","발주가 이루어진 연월 (YYYYMM)"),
    ("FACT_REPLENISHMENT_ORDER","ORDER_DT",      "발주일",       "CHAR(8)",    "N","N","N","","실제 발주가 이루어진 날짜 (YYYYMMDD)"),
    ("FACT_REPLENISHMENT_ORDER","PROMISED_DT",   "납품예정일",   "CHAR(8)",    "N","N","N","","공급업체가 약속한 납품 예정일 = ORDER_DT + LT"),
    ("FACT_REPLENISHMENT_ORDER","ACTUAL_DT",     "실납품일",     "CHAR(8)",    "Y","N","N","","실제 납품이 완료된 날짜 (미납=공백)"),
    ("FACT_REPLENISHMENT_ORDER","ORDER_QTY",     "발주수량",     "INTEGER",    "N","N","N","","발주한 수량"),
    ("FACT_REPLENISHMENT_ORDER","RECEIVED_QTY",  "수령수량",     "INTEGER",    "N","N","N","","실제 입고 수량 (부분납품 시 ORDER_QTY 미만)"),
    ("FACT_REPLENISHMENT_ORDER","UNIT_COST",     "단가",         "INTEGER",    "N","N","N","","발주 시점 부품 단가"),
    ("FACT_REPLENISHMENT_ORDER","CURRENCY",      "통화",         "CHAR(3)",    "N","N","N","","발주 통화 (KRW/USD)"),
    ("FACT_REPLENISHMENT_ORDER","ORDER_AMOUNT",  "발주금액",     "DECIMAL(14,2)","N","N","N","","ORDER_QTY × UNIT_COST (해당 통화)"),
    ("FACT_REPLENISHMENT_ORDER","DELAY_DAYS",    "지연일수",     "INTEGER",    "N","N","N","","ACTUAL_DT - PROMISED_DT (양수=지연, 음수=조기납품)"),
    ("FACT_REPLENISHMENT_ORDER","STATUS",        "발주상태",     "VARCHAR(10)","N","N","N","","DELIVERED/DELAYED/PARTIAL/PENDING"),
    # ── FACT_STOCKOUT_EVENT ──
    ("FACT_STOCKOUT_EVENT","STOCKOUT_ID",     "품절ID",       "VARCHAR(7)", "N","Y","N","","품절 이벤트 고유 ID"),
    ("FACT_STOCKOUT_EVENT","OFFICE_CD",       "지점코드",     "VARCHAR(8)", "N","N","Y","MST_OFFICE.OFFICE_CD","품절 발생 지점 FK"),
    ("FACT_STOCKOUT_EVENT","PART_CD",         "부품코드",     "VARCHAR(6)", "N","N","Y","MST_PART.PART_CD","품절 부품 FK"),
    ("FACT_STOCKOUT_EVENT","STOCKOUT_YM",     "품절발생년월", "CHAR(6)",    "N","N","N","","품절 발생 연월 (YYYYMM)"),
    ("FACT_STOCKOUT_EVENT","START_DT",        "품절시작일",   "CHAR(8)",    "N","N","N","","품절 시작일 (YYYYMMDD)"),
    ("FACT_STOCKOUT_EVENT","END_DT",          "품절종료일",   "CHAR(8)",    "N","N","N","","재고 회복일 (YYYYMMDD)"),
    ("FACT_STOCKOUT_EVENT","DURATION_DAYS",   "품절기간(일)", "INTEGER",    "N","N","N","","품절 지속 일수"),
    ("FACT_STOCKOUT_EVENT","LOST_SALES_QTY",  "기회손실수량", "INTEGER",    "N","N","N","","품절로 인해 판매하지 못한 추정 수량"),
    ("FACT_STOCKOUT_EVENT","CAUSE_CODE",      "원인코드",     "VARCHAR(20)","N","N","N","","품절 원인 분류 (LATE_DELIVERY/DEMAND_SURGE/FORECAST_ERROR/SUPPLIER_ISSUE/PORT_DELAY)"),
    ("FACT_STOCKOUT_EVENT","LINKED_ORDER_ID", "연결발주ID",   "VARCHAR(9)", "Y","N","Y","FACT_REPLENISHMENT_ORDER.ORDER_ID","원인이 된 발주 건 FK"),
]


# ═══════════════════════════════════════════════════════════════
# CSV 저장 헬퍼
# ═══════════════════════════════════════════════════════════════

def write_csv(filename, rows, fields=None):
    path = os.path.join(DATA_DIR, filename)
    if isinstance(rows[0], (list, tuple)):
        # 마스터 데이터: 튜플 리스트
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(fields)
            w.writerows(rows)
    else:
        # 딕셔너리 리스트
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)
    count = len(rows)
    print(f"  [OK] {filename:45s} ({count:,}행)")


if __name__ == "__main__":
    print("\n[ 바닐라코 공급망·리드타임 최적화 데모 데이터 생성 ]\n")

    write_csv("MST_OFFICE.csv",               OFFICES,       OFFICE_FIELDS)
    write_csv("MST_PART.csv",                 PARTS,         PART_FIELDS)
    write_csv("MST_SUPPLY_ROUTE.csv",         ROUTES,        ROUTE_FIELDS)
    write_csv("FACT_REPLENISHMENT_ORDER.csv", order_rows)
    write_csv("FACT_STOCKOUT_EVENT.csv",      stockout_rows)

    # DATA_DICTIONARY
    path = os.path.join(DATA_DIR, "DATA_DICTIONARY.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(DD_FIELDS)
        w.writerows(DATA_DICT)
    print(f"  [OK] {'DATA_DICTIONARY.csv':45s} ({len(DATA_DICT)}행)")

    print(f"\n  발주 이력 기간: 2022-01 ~ 2024-12 (36개월)")
    print(f"  품절 이벤트 수: {len(stockout_rows)}건")
    print("\n완료!")
