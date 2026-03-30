"""
자동차 부품 공급망(SCM) 재고관리 도메인 데모 데이터셋 생성기
출력: data/supply_chain/ 폴더에 CSV 6개 + SCHEMA_DEFINITION.json + LOGIC_DOCUMENT.txt

테이블 구성:
  - MST_PART         : 자동차 부품 마스터 (30종)
  - MST_SUPPLIER     : 공급업체 마스터 (10개)
  - MST_WAREHOUSE    : 창고/물류센터 마스터 (8개)
  - FACT_MONTHLY_DEMAND  : 월별 수요 실적 (2022-01 ~ 2024-12)
  - FACT_INVENTORY       : 분기별 재고 스냅샷
  - FACT_ORDER           : 구매발주 이력 (~3000-4000건)
  - SCHEMA_DEFINITION.json
  - LOGIC_DOCUMENT.txt
"""

import csv
import json
import os
import random
from datetime import date, timedelta
from collections import Counter

random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "supply_chain")
os.makedirs(DATA_DIR, exist_ok=True)


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def write_csv(filename: str, rows: list):
    """rows(list of dict)를 DATA_DIR/filename 으로 저장"""
    if not rows:
        return
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def rand_date(start: date, end: date) -> date:
    """start ~ end 사이 임의의 날짜 반환"""
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


# ── 마스터 데이터 정의 ────────────────────────────────────────────────────────

# MST_SUPPLIER (10개)
# (SUPPLIER_ID, SUPPLIER_NAME, SUPPLIER_TYPE, COUNTRY, LEAD_TIME_DAYS, MOQ, RELIABILITY_PCT, PAYMENT_TERMS)
SUPPLIERS = [
    ("SUP001", "현대모비스(주)",          "1차", "KR",  5,  10, 98, "NET30"),
    ("SUP002", "만도(주)",                "1차", "KR",  7,  10, 97, "NET30"),
    ("SUP003", "한국델파이(주)",          "1차", "KR",  6,   5, 96, "NET45"),
    ("SUP004", "덴소코리아(주)",          "1차", "JP", 18,   5, 94, "NET45"),
    ("SUP005", "아이신정기코리아",        "2차", "JP", 21,  10, 93, "NET60"),
    ("SUP006", "보쉬코리아(주)",          "1차", "DE", 20,   5, 95, "NET45"),
    ("SUP007", "콘티넨탈오토모티브코리아","1차", "DE", 22,   5, 93, "NET60"),
    ("SUP008", "닝보오토파츠(주)",        "2차", "CN", 28,  50, 88, "NET60"),
    ("SUP009", "상해정밀부품공사",        "3차", "CN", 32, 100, 85, "NET90"),
    ("SUP010", "광주솔루션(주)",          "2차", "KR",  4,  20, 97, "NET30"),
]

# SUPPLIER_ID → COUNTRY 빠른 조회용
SUP_COUNTRY = {s[0]: s[3] for s in SUPPLIERS}
SUP_LT      = {s[0]: s[4] for s in SUPPLIERS}

# MST_WAREHOUSE (8개)
# (WAREHOUSE_ID, WAREHOUSE_NAME, WAREHOUSE_TYPE, REGION, CAPACITY_UNITS, MANAGER_NAME, STATUS)
WAREHOUSES = [
    ("WH001", "평택 중앙물류센터",    "중앙물류센터", "수도권", 500000, "김정훈", "ACTIVE"),
    ("WH002", "인천 물류허브",        "중앙물류센터", "수도권", 300000, "이민수", "ACTIVE"),
    ("WH003", "부산 지역창고",        "지역창고",     "부산",   150000, "박진영", "ACTIVE"),
    ("WH004", "대구 지역창고",        "지역창고",     "대구",   120000, "최성훈", "ACTIVE"),
    ("WH005", "광주 지역창고",        "지역창고",     "광주",   100000, "정민지", "ACTIVE"),
    ("WH006", "대전 AS센터",          "직영AS센터",   "대전",    50000, "한상원", "ACTIVE"),
    ("WH007", "서울 딜러창고",        "딜러창고",     "수도권",  30000, "조현우", "ACTIVE"),
    ("WH008", "싱가포르 해외거점",    "지역창고",     "해외",    80000, "David Kim", "ACTIVE"),
]

WH_IDS = [w[0] for w in WAREHOUSES]

# 창고별 수요 가중치 (규모/지역 반영)
WH_WEIGHT = {
    "WH001": 1.0,   # 평택 중앙 — 기준
    "WH002": 0.75,  # 인천 허브
    "WH003": 0.45,  # 부산 지역
    "WH004": 0.35,  # 대구 지역
    "WH005": 0.30,  # 광주 지역
    "WH006": 0.15,  # 대전 AS센터
    "WH007": 0.10,  # 서울 딜러
    "WH008": 0.20,  # 싱가포르 해외
}

# MST_PART (30개)
# (PART_ID, PART_NAME, PART_CLASS, PART_TYPE, DEMAND_TYPE, CATEGORY,
#  UNIT_COST_KRW, STD_MONTHLY_DEMAND, LEAD_TIME_DAYS, MOQ, SUPPLIER_ID, STATUS)
PARTS = [
    # ── A급 10개 (고가·고중요도) ──────────────────────────────────────────────
    ("PT001", "엔진블록 어셈블리",    "A", "완성품부품", "INTERMITTENT", "엔진",  1_800_000,  30,  14,  1, "SUP001", "ACTIVE"),
    ("PT002", "트랜스미션 어셈블리",  "A", "완성품부품", "INTERMITTENT", "변속기",2_000_000,  20,  21,  1, "SUP004", "ACTIVE"),
    ("PT003", "터보차저",             "A", "완성품부품", "INTERMITTENT", "엔진",    850_000,  40,  18,  2, "SUP006", "ACTIVE"),
    ("PT004", "ECU 제어모듈",         "A", "완성품부품", "INTERMITTENT", "전장",    620_000,  60,  14,  2, "SUP007", "ACTIVE"),
    ("PT005", "인젝터 세트",          "A", "완성품부품", "KIT",          "엔진",    380_000,  80,  14,  4, "SUP004", "ACTIVE"),
    ("PT006", "브레이크 캘리퍼",      "A", "완성품부품", "REORDER",      "샤시",    220_000, 120,  10,  4, "SUP002", "ACTIVE"),
    ("PT007", "조향 기어박스",        "A", "완성품부품", "INTERMITTENT", "샤시",    480_000,  50,  18,  2, "SUP001", "ACTIVE"),
    ("PT008", "ABS 모듈",             "A", "완성품부품", "INTERMITTENT", "전장",    320_000,  70,  14,  2, "SUP007", "ACTIVE"),
    ("PT009", "에어백 어셈블리",      "A", "AS전용",     "INTERMITTENT", "차체",    250_000,  90,  10,  4, "SUP001", "ACTIVE"),
    ("PT010", "배터리 팩",            "A", "완성품부품", "SEASONAL",     "전장",    950_000,  40,  14,  1, "SUP003", "ACTIVE"),

    # ── B급 12개 (중간 중요도) ───────────────────────────────────────────────
    ("PT011", "에어필터",             "B", "소모품", "REORDER",   "엔진",   18_000, 800,  7, 20, "SUP010", "ACTIVE"),
    ("PT012", "오일필터",             "B", "소모품", "REORDER",   "엔진",   12_000, 900,  5, 20, "SUP010", "ACTIVE"),
    ("PT013", "스파크플러그",         "B", "소모품", "REORDER",   "엔진",    8_000, 600,  5, 20, "SUP003", "ACTIVE"),
    ("PT014", "타이밍 벨트",          "B", "소모품", "REORDER",   "엔진",   65_000, 300,  7, 10, "SUP005", "ACTIVE"),
    ("PT015", "쿨런트 호스",          "B", "소모품", "SEASONAL",  "엔진",   22_000, 400,  7, 10, "SUP010", "ACTIVE"),
    ("PT016", "서스펜션 링크",        "B", "완성품부품", "REORDER","샤시",   95_000, 200, 10,  4, "SUP002", "ACTIVE"),
    ("PT017", "허브 베어링",          "B", "완성품부품", "REORDER","샤시",   48_000, 350,  7,  8, "SUP005", "ACTIVE"),
    ("PT018", "디스크 로터",          "B", "완성품부품", "REORDER","샤시",   78_000, 280,  7,  4, "SUP002", "ACTIVE"),
    ("PT019", "점화코일",             "B", "소모품", "REORDER",   "전장",   55_000, 250,  7, 10, "SUP003", "ACTIVE"),
    ("PT020", "산소센서",             "B", "소모품", "REORDER",   "전장",   42_000, 300,  7, 10, "SUP006", "ACTIVE"),
    ("PT021", "라디에이터",           "B", "완성품부품", "SEASONAL","엔진",  185_000, 150, 14,  2, "SUP008", "ACTIVE"),
    ("PT022", "워터펌프",             "B", "완성품부품", "SEASONAL","엔진",   68_000, 200, 10,  4, "SUP005", "ACTIVE"),

    # ── C급 8개 (저가·소모성) ────────────────────────────────────────────────
    ("PT023", "드레인플러그",         "C", "소모품", "REORDER",   "엔진",    1_500, 3000,  3, 100, "SUP010", "ACTIVE"),
    ("PT024", "에어컨 필터",          "C", "소모품", "SEASONAL",  "전장",    8_500, 1200,  5,  50, "SUP009", "ACTIVE"),
    ("PT025", "와이퍼블레이드",       "C", "소모품", "SEASONAL",  "차체",   12_000, 1500,  5,  50, "SUP009", "ACTIVE"),
    ("PT026", "전구류",               "C", "소모품", "REORDER",   "전장",    3_500, 2000,  3, 100, "SUP010", "ACTIVE"),
    ("PT027", "클립 세트",            "C", "소모품", "REORDER",   "차체",      800, 5000,  3, 200, "SUP009", "ACTIVE"),
    ("PT028", "실링 키트",            "C", "소모품", "KIT",       "엔진",    6_000, 1800,  5,  50, "SUP010", "ACTIVE"),
    ("PT029", "개스킷",               "C", "소모품", "KIT",       "엔진",    4_500, 2200,  3, 100, "SUP009", "ACTIVE"),
    ("PT030", "볼트 세트",            "C", "소모품", "REORDER",   "차체",    2_200, 4000,  3, 200, "SUP010", "ACTIVE"),
]

PART_IDS        = [p[0] for p in PARTS]
PART_DEMAND_TYPE = {p[0]: p[4]  for p in PARTS}
PART_COST       = {p[0]: p[6]  for p in PARTS}
PART_STD_DEMAND = {p[0]: p[7]  for p in PARTS}
PART_CLASS      = {p[0]: p[2]  for p in PARTS}
PART_SUPPLIER   = {p[0]: p[10] for p in PARTS}

# 월 목록 (2022-01 ~ 2024-12 = 36개월)
YEAR_MONTHS = []
for year in [2022, 2023, 2024]:
    for month in range(1, 13):
        YEAR_MONTHS.append(f"{year}-{month:02d}")

# 분기별 스냅샷 날짜 (분기말)
QUARTERLY_SNAPSHOTS = [
    "2022-03-31", "2022-06-30", "2022-09-30", "2022-12-31",
    "2023-03-31", "2023-06-30", "2023-09-30", "2023-12-31",
    "2024-03-31", "2024-06-30", "2024-09-30", "2024-12-31",
]

# 월별 계절 계수 (월 숫자 → 계수)
# 냉각계/에어컨: 여름(6~8월) 성수기, 배터리/히터: 겨울(11~2월) 성수기
def seasonal_factor(ym: str, demand_type: str, part_id: str) -> float:
    month = int(ym.split("-")[1])
    # 기본 계수
    base = 1.0
    if demand_type == "SEASONAL":
        # 냉각계(라디에이터, 워터펌프, 쿨런트호스, 에어컨필터): 여름 피크
        if part_id in ("PT015", "PT021", "PT022", "PT024"):
            summer = {6: 1.6, 7: 1.8, 8: 1.7, 5: 1.2, 9: 1.2}
            winter = {12: 0.7, 1: 0.6, 2: 0.7}
            base = summer.get(month, winter.get(month, 1.0))
        # 배터리팩, 와이퍼: 겨울/우기 피크
        elif part_id in ("PT010", "PT025"):
            winter = {11: 1.4, 12: 1.7, 1: 1.8, 2: 1.5}
            summer = {7: 1.2, 8: 1.3}
            base = winter.get(month, summer.get(month, 1.0))
    elif demand_type == "REORDER":
        # 소모품은 연말·연초 약간 증가 (정기점검 시즌)
        if month in (3, 9):    # 봄/가을 정기점검
            base = 1.2
        elif month in (1, 2):  # 연초 물량 조정
            base = 0.9
    return base


# ── 1. MST_SUPPLIER ───────────────────────────────────────────────────────────

def gen_mst_supplier():
    rows = []
    for (sid, sname, stype, country, lt, moq, rel, pay) in SUPPLIERS:
        rows.append({
            "SUPPLIER_ID":      sid,
            "SUPPLIER_NAME":    sname,
            "SUPPLIER_TYPE":    stype,
            "COUNTRY":          country,
            "LEAD_TIME_DAYS":   lt,
            "MOQ":              moq,
            "RELIABILITY_PCT":  rel,
            "PAYMENT_TERMS":    pay,
        })
    write_csv("MST_SUPPLIER.csv", rows)
    print(f"  MST_SUPPLIER.csv        - {len(rows)}행")


# ── 2. MST_WAREHOUSE ──────────────────────────────────────────────────────────

def gen_mst_warehouse():
    rows = []
    for (wid, wname, wtype, region, cap, manager, status) in WAREHOUSES:
        rows.append({
            "WAREHOUSE_ID":    wid,
            "WAREHOUSE_NAME":  wname,
            "WAREHOUSE_TYPE":  wtype,
            "REGION":          region,
            "CAPACITY_UNITS":  cap,
            "MANAGER_NAME":    manager,
            "STATUS":          status,
        })
    write_csv("MST_WAREHOUSE.csv", rows)
    print(f"  MST_WAREHOUSE.csv       - {len(rows)}행")


# ── 3. MST_PART ───────────────────────────────────────────────────────────────

def gen_mst_part():
    rows = []
    for (pid, pname, pclass, ptype, dtype, cat, cost, std_dem, lt, moq, sup, status) in PARTS:
        rows.append({
            "PART_ID":             pid,
            "PART_NAME":           pname,
            "PART_CLASS":          pclass,
            "PART_TYPE":           ptype,
            "DEMAND_TYPE":         dtype,
            "CATEGORY":            cat,
            "UNIT_COST_KRW":       cost,
            "STD_MONTHLY_DEMAND":  std_dem,
            "LEAD_TIME_DAYS":      lt,
            "MOQ":                 moq,
            "SUPPLIER_ID":         sup,
            "STATUS":              status,
        })
    write_csv("MST_PART.csv", rows)
    print(f"  MST_PART.csv            - {len(rows)}행")


# ── 4. FACT_MONTHLY_DEMAND ────────────────────────────────────────────────────

# 부품-창고 현실적 매핑
# 모든 창고에 모든 부품이 있지 않음: A급은 중앙물류+지역창고, AS전용은 AS센터 위주
def part_wh_applicable(part_id: str, wh_id: str) -> bool:
    pclass = PART_CLASS[part_id]
    ptype  = next(p[3] for p in PARTS if p[0] == part_id)
    # AS전용 부품 → AS센터(WH006) + 딜러창고(WH007) + 중앙(WH001, WH002) 위주
    if ptype == "AS전용":
        return wh_id in ("WH001", "WH002", "WH006", "WH007")
    # A급 완성품부품 → 중앙물류 + 주요 지역창고 (해외 제외)
    if pclass == "A":
        return wh_id in ("WH001", "WH002", "WH003", "WH004", "WH005", "WH006")
    # B급 → 전 창고
    if pclass == "B":
        return True
    # C급 소모품 → 딜러창고/AS센터 포함 전창고
    return True


def gen_fact_monthly_demand():
    rows = []
    demand_id = 1
    # 수요 기록 (재고 스냅샷 계산에 재활용)
    demand_map = {}  # (part_id, wh_id, ym) → qty

    for ym in YEAR_MONTHS:
        for part in PARTS:
            pid        = part[0]
            base_dem   = part[7]
            dtype      = part[4]
            cost       = part[6]

            for wh in WAREHOUSES:
                wh_id = wh[0]
                if not part_wh_applicable(pid, wh_id):
                    continue

                ww = WH_WEIGHT[wh_id]
                sf = seasonal_factor(ym, dtype, pid)

                # 수요 유형별 수량 결정
                if dtype == "INTERMITTENT":
                    # 60% 확률로 수요 없음
                    if random.random() < 0.60:
                        qty = 0
                    else:
                        qty = max(1, int(base_dem * ww * sf * random.uniform(0.5, 2.0)))
                elif dtype == "KIT":
                    # 키트 수요: 대체로 안정적이나 주 부품과 연동 스파이크
                    spike = 1.5 if random.random() < 0.15 else 1.0
                    qty = max(0, int(base_dem * ww * sf * spike * random.uniform(0.85, 1.15)))
                else:
                    # REORDER / SEASONAL: 기본 노이즈 ±10%
                    qty = max(0, int(base_dem * ww * sf * random.uniform(0.90, 1.10)))

                # 예측 수량: 실수요 ±15%, 20% 확률로 NULL
                if random.random() < 0.20:
                    forecast_qty = None
                    forecast_err = None
                else:
                    forecast_qty = max(0, int(qty * random.uniform(0.85, 1.15)))
                    if forecast_qty > 0 and qty > 0:
                        forecast_err = round(abs(forecast_qty - qty) / qty * 100, 2)
                    else:
                        forecast_err = None

                # 수요 유형 실적
                if qty == 0:
                    actual_dtype = "REGULAR"
                elif random.random() < 0.08:
                    actual_dtype = "EMERGENCY"
                elif next(p[3] for p in PARTS if p[0] == pid) == "AS전용":
                    actual_dtype = "AS"
                elif dtype == "KIT":
                    actual_dtype = "KIT"
                else:
                    actual_dtype = "REGULAR"

                demand_amount = qty * cost

                rows.append({
                    "DEMAND_ID":          f"DMD{demand_id:06d}",
                    "PART_ID":            pid,
                    "WAREHOUSE_ID":       wh_id,
                    "YEAR_MONTH":         ym,
                    "DEMAND_TYPE_ACTUAL": actual_dtype,
                    "DEMAND_QTY":         qty,
                    "FORECAST_QTY":       forecast_qty,
                    "FORECAST_ERROR_PCT": forecast_err,
                    "UNIT_COST_KRW":      cost,
                    "DEMAND_AMOUNT_KRW":  demand_amount,
                })
                demand_map[(pid, wh_id, ym)] = qty
                demand_id += 1

    write_csv("FACT_MONTHLY_DEMAND.csv", rows)
    null_forecast = sum(1 for r in rows if r["FORECAST_QTY"] is None)
    print(f"  FACT_MONTHLY_DEMAND.csv - {len(rows)}행  |  예측NULL: {null_forecast}건({null_forecast/len(rows)*100:.1f}%)")
    return demand_map


# ── 5. FACT_INVENTORY ─────────────────────────────────────────────────────────

def gen_fact_inventory(demand_map: dict):
    rows = []
    inv_id = 1

    for snap_date_str in QUARTERLY_SNAPSHOTS:
        snap_date = date.fromisoformat(snap_date_str)
        # 해당 분기의 마지막 달 찾기
        ym = f"{snap_date.year}-{snap_date.month:02d}"

        for part in PARTS:
            pid    = part[0]
            cost   = part[6]
            lt     = part[8]     # LEAD_TIME_DAYS
            pclass = part[2]
            dtype  = part[4]

            for wh in WAREHOUSES:
                wh_id = wh[0]
                if not part_wh_applicable(pid, wh_id):
                    continue

                # 최근 3개월 평균 수요 계산 (스냅샷 기준 직전 3개월)
                recent_yms = []
                m = snap_date.month
                y = snap_date.year
                for _ in range(3):
                    recent_yms.append(f"{y}-{m:02d}")
                    m -= 1
                    if m == 0:
                        m = 12
                        y -= 1

                monthly_demands = [demand_map.get((pid, wh_id, tym), 0) for tym in recent_yms]
                avg_monthly_dem = sum(monthly_demands) / 3 if monthly_demands else 0
                daily_dem = avg_monthly_dem / 30

                # 서비스 수준 z-score: A급 1.65 (99%), B급 1.44 (97%), C급 1.64 (95%)
                z = {"A": 1.65, "B": 1.44, "C": 1.36}.get(pclass, 1.65)
                review_period = {"A": 14, "B": 21, "C": 30}.get(pclass, 14)  # days

                # 수요 표준편차 근사 (±10% 기준)
                std_dem_daily = daily_dem * 0.10 if daily_dem > 0 else 1
                safety_stock = max(1, int(z * std_dem_daily * ((lt + review_period) ** 0.5)))

                # AS센터는 안전재고 1.5배 유지
                if wh[2] == "직영AS센터":
                    safety_stock = int(safety_stock * 1.5)

                reorder_point = int(safety_stock + daily_dem * lt)

                # 현재고: 재주문점 기준 0.3배 ~ 3.0배 (현실적 분포)
                stock_qty = max(0, int(reorder_point * random.uniform(0.3, 3.0)))

                # 재고 상태 결정
                if stock_qty == 0:
                    status = "STOCKOUT"
                elif stock_qty < safety_stock:
                    status = "CRITICAL"
                elif stock_qty < reorder_point:
                    status = "LOW"
                elif stock_qty < reorder_point * 2.5:
                    status = "NORMAL"
                else:
                    status = "OVERSTOCK"

                inventory_value = stock_qty * cost

                # 마지막 이동일: 15% 확률로 NULL
                if random.random() < 0.15:
                    last_movement = None
                else:
                    days_ago = random.randint(1, 90)
                    last_movement = str(snap_date - timedelta(days=days_ago))

                rows.append({
                    "INVENTORY_ID":        f"INV{inv_id:06d}",
                    "PART_ID":             pid,
                    "WAREHOUSE_ID":        wh_id,
                    "SNAPSHOT_DATE":       snap_date_str,
                    "STOCK_QTY":           stock_qty,
                    "SAFETY_STOCK_QTY":    safety_stock,
                    "REORDER_POINT":       reorder_point,
                    "STOCK_STATUS":        status,
                    "INVENTORY_VALUE_KRW": inventory_value,
                    "LAST_MOVEMENT_DATE":  last_movement,
                })
                inv_id += 1

    write_csv("FACT_INVENTORY.csv", rows)
    status_dist = Counter(r["STOCK_STATUS"] for r in rows)
    null_mvt = sum(1 for r in rows if r["LAST_MOVEMENT_DATE"] is None)
    print(f"  FACT_INVENTORY.csv      - {len(rows)}행  |  상태분포: {dict(status_dist)}  |  이동일NULL: {null_mvt}건")
    return rows


# ── 6. FACT_ORDER ─────────────────────────────────────────────────────────────

def gen_fact_order():
    rows = []
    order_id = 1

    start_date = date(2022, 1, 1)
    end_date   = date(2024, 12, 31)

    # 부품별 발주 빈도 가중치 (A급 고가 → 소량·소발주, C급 소모품 → 대량·빈발주)
    class_order_freq = {"A": 8, "B": 5, "C": 3}   # 발주당 평균 개월 간격 역수 개념
    class_order_qty_mult = {"A": 1.0, "B": 2.0, "C": 5.0}

    order_types = ["REGULAR", "REGULAR", "REGULAR", "EMERGENCY", "BLANKET"]  # 가중치용

    # 각 부품-창고 조합에 대해 발주 이력 생성
    # 총 ~3000-4000건 목표 → 부품×창고 조합 수에 맞게 조정
    applicable_combos = []
    for part in PARTS:
        for wh in WAREHOUSES:
            if part_wh_applicable(part[0], wh[0]):
                applicable_combos.append((part[0], wh[0]))

    # 조합당 평균 발주 수 계산 (3년간)
    # ~3500건 목표 / combo 수
    n_combos = len(applicable_combos)
    avg_orders_per_combo = max(3, int(3500 / n_combos))

    for (pid, wh_id) in applicable_combos:
        pclass      = PART_CLASS[pid]
        sup_id      = PART_SUPPLIER[pid]
        base_cost   = PART_COST[pid]
        lt_days     = next(p[8] for p in PARTS if p[0] == pid)
        moq         = next(p[9] for p in PARTS if p[0] == pid)
        std_dem     = PART_STD_DEMAND[pid]
        country     = SUP_COUNTRY[sup_id]
        ww          = WH_WEIGHT[wh_id]

        n_orders = max(2, int(avg_orders_per_combo * random.uniform(0.6, 1.4)))

        for _ in range(n_orders):
            order_date = rand_date(start_date, end_date)

            # 발주 유형
            order_type = random.choice(order_types)
            if order_type == "EMERGENCY":
                lt_actual_days = max(1, lt_days // 2)  # 긴급은 절반 리드타임
            else:
                lt_actual_days = lt_days

            promised_date = order_date + timedelta(days=lt_actual_days)

            # 발주 수량: MOQ 단위, 수요 × 창고 가중치 × 2~4개월치
            coverage_months = random.uniform(2.0, 4.0)
            raw_qty = std_dem * ww * coverage_months * class_order_qty_mult[pclass]
            order_qty = max(moq, int(raw_qty / moq) * moq)

            # 단가 ±5% 변동
            unit_cost = max(1, int(base_cost * random.uniform(0.95, 1.05)))
            order_amount = order_qty * unit_cost

            # 국가별 지연 패턴
            if country == "KR":
                delay_days = random.randint(0, 3) if random.random() < 0.90 else random.randint(4, 10)
            elif country in ("JP", "DE"):
                delay_days = random.randint(0, 5) if random.random() < 0.70 else random.randint(5, 15)
            else:  # CN
                delay_days = random.randint(0, 7) if random.random() < 0.55 else random.randint(10, 30)

            actual_delivery = promised_date + timedelta(days=delay_days)

            # 5% 취소
            if random.random() < 0.05:
                status = "CANCELLED"
                actual_date   = None
                received_qty  = 0
                delay_days    = 0
            elif actual_delivery > date.today():
                # 미래 날짜 → PENDING
                status = "PENDING"
                actual_date  = None
                received_qty = 0
            elif delay_days > 7:
                # 8% 부분납품
                if random.random() < 0.08:
                    status = "PARTIAL"
                    received_qty = int(order_qty * random.uniform(0.5, 0.9))
                    actual_date  = str(actual_delivery)
                else:
                    status = "DELAYED"
                    received_qty = order_qty
                    actual_date  = str(actual_delivery)
            else:
                status = "DELIVERED"
                received_qty = order_qty
                actual_date  = str(actual_delivery)
                delay_days   = 0  # 정시 납품은 지연 0

            rows.append({
                "ORDER_ID":         f"ORD{order_id:06d}",
                "PART_ID":          pid,
                "SUPPLIER_ID":      sup_id,
                "WAREHOUSE_ID":     wh_id,
                "ORDER_DATE":       str(order_date),
                "PROMISED_DATE":    str(promised_date),
                "ACTUAL_DATE":      actual_date,
                "ORDER_QTY":        order_qty,
                "RECEIVED_QTY":     received_qty,
                "UNIT_COST_KRW":    unit_cost,
                "ORDER_AMOUNT_KRW": order_amount,
                "DELAY_DAYS":       delay_days,
                "ORDER_TYPE":       order_type,
                "STATUS":           status,
            })
            order_id += 1

    # 날짜순 정렬
    rows.sort(key=lambda r: r["ORDER_DATE"])
    # ORDER_ID 재부여
    for i, r in enumerate(rows, 1):
        r["ORDER_ID"] = f"ORD{i:06d}"

    write_csv("FACT_ORDER.csv", rows)
    status_dist = Counter(r["STATUS"] for r in rows)
    print(f"  FACT_ORDER.csv          - {len(rows)}행  |  상태분포: {dict(status_dist)}")
    return rows


# ── 7. SCHEMA_DEFINITION.json ─────────────────────────────────────────────────

def write_schema_json():
    SCHEMA = {
        "domain": "자동차 부품 공급망 재고관리 (Automotive Parts SCM)",
        "data_range": "2022-01 ~ 2024-12 (3년)",
        "tables": [
            {
                "table_name": "MST_PART",
                "table_type": "master_table",
                "description": "자동차 부품 마스터 — 30종 부품의 기본 정보, ABC 등급, 수요유형, 단가",
                "row_count_approx": 30,
                "columns": [
                    {"name": "PART_ID",            "type": "VARCHAR(10)",  "pk": True,  "nullable": False, "description": "부품 고유 ID (PK). PT001~PT030"},
                    {"name": "PART_NAME",           "type": "VARCHAR(100)", "pk": False, "nullable": False, "description": "부품명 (한국어)"},
                    {"name": "PART_CLASS",          "type": "CHAR(1)",      "pk": False, "nullable": False, "description": "ABC 등급. A=고가/고중요, B=중간, C=소모성"},
                    {"name": "PART_TYPE",           "type": "VARCHAR(20)",  "pk": False, "nullable": False, "description": "부품 유형: 완성품부품/소모품/AS전용"},
                    {"name": "DEMAND_TYPE",         "type": "VARCHAR(20)",  "pk": False, "nullable": False, "description": "수요 패턴 유형: SEASONAL/REORDER/INTERMITTENT/KIT"},
                    {"name": "CATEGORY",            "type": "VARCHAR(20)",  "pk": False, "nullable": False, "description": "부품 계통: 엔진/변속기/샤시/전장/차체"},
                    {"name": "UNIT_COST_KRW",       "type": "INTEGER",      "pk": False, "nullable": False, "description": "부품 단가 (원)"},
                    {"name": "STD_MONTHLY_DEMAND",  "type": "INTEGER",      "pk": False, "nullable": False, "description": "기준 월 수요량 (전사 합계 기준)"},
                    {"name": "LEAD_TIME_DAYS",      "type": "INTEGER",      "pk": False, "nullable": False, "description": "조달 리드타임 (일)"},
                    {"name": "MOQ",                 "type": "INTEGER",      "pk": False, "nullable": False, "description": "최소 발주 수량 (Minimum Order Quantity)"},
                    {"name": "SUPPLIER_ID",         "type": "VARCHAR(10)",  "pk": False, "nullable": False, "description": "주 공급업체 ID (FK → MST_SUPPLIER.SUPPLIER_ID)"},
                    {"name": "STATUS",              "type": "VARCHAR(10)",  "pk": False, "nullable": False, "description": "부품 상태: ACTIVE/OBSOLETE"},
                ],
            },
            {
                "table_name": "MST_SUPPLIER",
                "table_type": "master_table",
                "description": "공급업체 마스터 — 10개 공급사의 국가, 리드타임, 신뢰도",
                "row_count_approx": 10,
                "columns": [
                    {"name": "SUPPLIER_ID",     "type": "VARCHAR(10)",  "pk": True,  "nullable": False, "description": "공급업체 ID (PK). SUP001~SUP010"},
                    {"name": "SUPPLIER_NAME",   "type": "VARCHAR(100)", "pk": False, "nullable": False, "description": "공급업체명"},
                    {"name": "SUPPLIER_TYPE",   "type": "VARCHAR(5)",   "pk": False, "nullable": False, "description": "공급 단계: 1차/2차/3차"},
                    {"name": "COUNTRY",         "type": "CHAR(2)",      "pk": False, "nullable": False, "description": "소재 국가: KR/JP/DE/CN"},
                    {"name": "LEAD_TIME_DAYS",  "type": "INTEGER",      "pk": False, "nullable": False, "description": "평균 조달 리드타임 (일)"},
                    {"name": "MOQ",             "type": "INTEGER",      "pk": False, "nullable": False, "description": "최소 발주 수량"},
                    {"name": "RELIABILITY_PCT", "type": "INTEGER",      "pk": False, "nullable": False, "description": "납기 신뢰도 (%). 범위: 85~99"},
                    {"name": "PAYMENT_TERMS",   "type": "VARCHAR(10)",  "pk": False, "nullable": False, "description": "결제 조건: NET30/NET45/NET60/NET90"},
                ],
            },
            {
                "table_name": "MST_WAREHOUSE",
                "table_type": "master_table",
                "description": "창고/물류센터 마스터 — 8개 거점의 유형, 지역, 용량",
                "row_count_approx": 8,
                "columns": [
                    {"name": "WAREHOUSE_ID",    "type": "VARCHAR(10)",  "pk": True,  "nullable": False, "description": "창고 ID (PK). WH001~WH008"},
                    {"name": "WAREHOUSE_NAME",  "type": "VARCHAR(100)", "pk": False, "nullable": False, "description": "창고명"},
                    {"name": "WAREHOUSE_TYPE",  "type": "VARCHAR(20)",  "pk": False, "nullable": False, "description": "창고 유형: 중앙물류센터/지역창고/직영AS센터/딜러창고"},
                    {"name": "REGION",          "type": "VARCHAR(20)",  "pk": False, "nullable": False, "description": "권역: 수도권/부산/대구/광주/대전/해외"},
                    {"name": "CAPACITY_UNITS",  "type": "INTEGER",      "pk": False, "nullable": False, "description": "총 보관 가능 수량 (단위)"},
                    {"name": "MANAGER_NAME",    "type": "VARCHAR(50)",  "pk": False, "nullable": False, "description": "담당 관리자명"},
                    {"name": "STATUS",          "type": "VARCHAR(10)",  "pk": False, "nullable": False, "description": "운영 상태: ACTIVE/INACTIVE"},
                ],
            },
            {
                "table_name": "FACT_MONTHLY_DEMAND",
                "table_type": "fact_table",
                "description": "월별 수요 실적 팩트 — 부품×창고별 월간 수요량, 예측량, 수요금액 (2022-2024)",
                "columns": [
                    {"name": "DEMAND_ID",          "type": "VARCHAR(12)",  "pk": True,  "nullable": False, "description": "수요 레코드 ID (PK). DMD + 6자리"},
                    {"name": "PART_ID",            "type": "VARCHAR(10)",  "pk": False, "nullable": False, "description": "부품 ID (FK → MST_PART.PART_ID)"},
                    {"name": "WAREHOUSE_ID",       "type": "VARCHAR(10)",  "pk": False, "nullable": False, "description": "창고 ID (FK → MST_WAREHOUSE.WAREHOUSE_ID)"},
                    {"name": "YEAR_MONTH",         "type": "VARCHAR(7)",   "pk": False, "nullable": False, "description": "집계 연월 (YYYY-MM)"},
                    {"name": "DEMAND_TYPE_ACTUAL", "type": "VARCHAR(15)",  "pk": False, "nullable": False, "description": "실제 수요 유형: REGULAR/AS/KIT/EMERGENCY"},
                    {"name": "DEMAND_QTY",         "type": "INTEGER",      "pk": False, "nullable": False, "description": "실수요 수량"},
                    {"name": "FORECAST_QTY",       "type": "INTEGER",      "pk": False, "nullable": True,  "description": "예측 수량. NULL=예측 미수행(약 20%)"},
                    {"name": "FORECAST_ERROR_PCT", "type": "DECIMAL(6,2)", "pk": False, "nullable": True,  "description": "예측 오차율(%). |예측-실수요|/실수요×100. NULL 가능"},
                    {"name": "UNIT_COST_KRW",      "type": "INTEGER",      "pk": False, "nullable": False, "description": "부품 단가 (원)"},
                    {"name": "DEMAND_AMOUNT_KRW",  "type": "BIGINT",       "pk": False, "nullable": False, "description": "수요 금액 = DEMAND_QTY × UNIT_COST_KRW"},
                ],
            },
            {
                "table_name": "FACT_INVENTORY",
                "table_type": "fact_table",
                "description": "분기별 재고 스냅샷 팩트 — 분기말 기준 부품×창고별 재고량, 안전재고, 재고상태",
                "columns": [
                    {"name": "INVENTORY_ID",        "type": "VARCHAR(12)", "pk": True,  "nullable": False, "description": "재고 스냅샷 ID (PK). INV + 6자리"},
                    {"name": "PART_ID",             "type": "VARCHAR(10)", "pk": False, "nullable": False, "description": "부품 ID (FK → MST_PART.PART_ID)"},
                    {"name": "WAREHOUSE_ID",        "type": "VARCHAR(10)", "pk": False, "nullable": False, "description": "창고 ID (FK → MST_WAREHOUSE.WAREHOUSE_ID)"},
                    {"name": "SNAPSHOT_DATE",       "type": "DATE",        "pk": False, "nullable": False, "description": "스냅샷 기준일 (분기말: 3/31, 6/30, 9/30, 12/31)"},
                    {"name": "STOCK_QTY",           "type": "INTEGER",     "pk": False, "nullable": False, "description": "현재고 수량"},
                    {"name": "SAFETY_STOCK_QTY",    "type": "INTEGER",     "pk": False, "nullable": False, "description": "안전재고 수량. SS = z × σ_daily × √(LT + T)"},
                    {"name": "REORDER_POINT",       "type": "INTEGER",     "pk": False, "nullable": False, "description": "재주문점 = SAFETY_STOCK + 일평균수요 × LT"},
                    {"name": "STOCK_STATUS",        "type": "VARCHAR(15)", "pk": False, "nullable": False, "description": "재고상태: OVERSTOCK/NORMAL/LOW/CRITICAL/STOCKOUT"},
                    {"name": "INVENTORY_VALUE_KRW", "type": "BIGINT",      "pk": False, "nullable": False, "description": "재고 금액 = STOCK_QTY × UNIT_COST_KRW"},
                    {"name": "LAST_MOVEMENT_DATE",  "type": "DATE",        "pk": False, "nullable": True,  "description": "최근 입출고 일자. NULL=이력 없음(약 15%)"},
                ],
            },
            {
                "table_name": "FACT_ORDER",
                "table_type": "fact_table",
                "description": "구매발주 이력 팩트 — 2022~2024 발주/납품 이력, 지연일수, 상태 (~3500건)",
                "columns": [
                    {"name": "ORDER_ID",         "type": "VARCHAR(12)",  "pk": True,  "nullable": False, "description": "발주 ID (PK). ORD + 6자리"},
                    {"name": "PART_ID",          "type": "VARCHAR(10)",  "pk": False, "nullable": False, "description": "부품 ID (FK → MST_PART.PART_ID)"},
                    {"name": "SUPPLIER_ID",      "type": "VARCHAR(10)",  "pk": False, "nullable": False, "description": "공급업체 ID (FK → MST_SUPPLIER.SUPPLIER_ID)"},
                    {"name": "WAREHOUSE_ID",     "type": "VARCHAR(10)",  "pk": False, "nullable": False, "description": "납품 창고 ID (FK → MST_WAREHOUSE.WAREHOUSE_ID)"},
                    {"name": "ORDER_DATE",       "type": "DATE",         "pk": False, "nullable": False, "description": "발주일"},
                    {"name": "PROMISED_DATE",    "type": "DATE",         "pk": False, "nullable": False, "description": "약정 납기일 = ORDER_DATE + LEAD_TIME_DAYS"},
                    {"name": "ACTUAL_DATE",      "type": "DATE",         "pk": False, "nullable": True,  "description": "실제 납품일. NULL=PENDING 또는 CANCELLED"},
                    {"name": "ORDER_QTY",        "type": "INTEGER",      "pk": False, "nullable": False, "description": "발주 수량"},
                    {"name": "RECEIVED_QTY",     "type": "INTEGER",      "pk": False, "nullable": False, "description": "실제 입고 수량. PARTIAL이면 ORDER_QTY 미만"},
                    {"name": "UNIT_COST_KRW",    "type": "INTEGER",      "pk": False, "nullable": False, "description": "발주 단가 (원). 기준가 ±5% 변동"},
                    {"name": "ORDER_AMOUNT_KRW", "type": "BIGINT",       "pk": False, "nullable": False, "description": "발주 금액 = ORDER_QTY × UNIT_COST_KRW"},
                    {"name": "DELAY_DAYS",       "type": "INTEGER",      "pk": False, "nullable": False, "description": "납기 지연일수. 0=정시납품"},
                    {"name": "ORDER_TYPE",       "type": "VARCHAR(15)",  "pk": False, "nullable": False, "description": "발주 유형: REGULAR/EMERGENCY/BLANKET"},
                    {"name": "STATUS",           "type": "VARCHAR(15)",  "pk": False, "nullable": False, "description": "발주 상태: DELIVERED/DELAYED/PARTIAL/PENDING/CANCELLED"},
                ],
            },
        ],
        "relationships": [
            {"from": "MST_PART",            "to": "MST_SUPPLIER",   "join_key": "SUPPLIER_ID",  "relation": "N:1",
             "description": "부품 → 주 공급업체"},
            {"from": "FACT_MONTHLY_DEMAND", "to": "MST_PART",       "join_key": "PART_ID",      "relation": "N:1",
             "description": "월별 수요 → 부품 마스터"},
            {"from": "FACT_MONTHLY_DEMAND", "to": "MST_WAREHOUSE",  "join_key": "WAREHOUSE_ID", "relation": "N:1",
             "description": "월별 수요 → 창고 마스터"},
            {"from": "FACT_INVENTORY",      "to": "MST_PART",       "join_key": "PART_ID",      "relation": "N:1",
             "description": "재고 스냅샷 → 부품 마스터"},
            {"from": "FACT_INVENTORY",      "to": "MST_WAREHOUSE",  "join_key": "WAREHOUSE_ID", "relation": "N:1",
             "description": "재고 스냅샷 → 창고 마스터"},
            {"from": "FACT_ORDER",          "to": "MST_PART",       "join_key": "PART_ID",      "relation": "N:1",
             "description": "발주 이력 → 부품 마스터"},
            {"from": "FACT_ORDER",          "to": "MST_SUPPLIER",   "join_key": "SUPPLIER_ID",  "relation": "N:1",
             "description": "발주 이력 → 공급업체 마스터"},
            {"from": "FACT_ORDER",          "to": "MST_WAREHOUSE",  "join_key": "WAREHOUSE_ID", "relation": "N:1",
             "description": "발주 이력 → 납품 창고 마스터"},
        ],
    }

    path = os.path.join(DATA_DIR, "SCHEMA_DEFINITION.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(SCHEMA, f, ensure_ascii=False, indent=2)
    print(f"  SCHEMA_DEFINITION.json  - 테이블 {len(SCHEMA['tables'])}개, 관계 {len(SCHEMA['relationships'])}개")


# ── 8. LOGIC_DOCUMENT.txt ─────────────────────────────────────────────────────

LOGIC_DOC = """\
================================================================
자동차 부품 공급망 재고 관리 전략 문서
작성 기준: 2025년 SCM 운영 정책 (자동차 부품 제조사)
================================================================

1. PART_CLASS별 재고 관리 정책 (ABC 분석)
----------------------------------------------------------------

[A급 — 전체 매출의 80%, 약 10종]  엔진블록, 트랜스미션, 터보차저, ECU 제어모듈 등 고가 핵심 부품
  - 관리 원칙: 엄격한 재고 통제, 개별 SKU 단위 면밀한 모니터링
  - 안전재고 공식: SS = z × σ_daily × √(LT + T)
      z = 1.65 (서비스 수준 99%)
      σ_daily = 일평균수요의 표준편차
      LT  = 조달 리드타임 (일)
      T   = 발주 검토 주기 (14일, 2주 단위)
  - 발주 주기: 2주 단위 정기 검토 (주기적 재주문 정책, R 정책)
  - 재주문점(ROP): SS + (일평균수요 × LT)
  - KPI 목표:
      * 서비스 수준(Service Level): 99% 이상
      * 재고 회전율(ITR): 연 12회 이상 (월 1회 이상 회전)
      * 납기 준수율: 97% 이상

[B급 — 매출 15%, 약 12종]  에어필터, 디스크 로터, 서스펜션 링크, 점화코일 등
  - 관리 원칙: 표준 정기 발주, 월 단위 재고 검토
  - 발주 주기: 3주 단위 정기 검토
  - 안전재고: z = 1.44 (서비스 수준 97%), 검토 주기 T = 21일
  - KPI 목표: 서비스 수준 97%, 재고회전율 연 8회

[C급 — 매출 5%, 약 8종]  드레인플러그, 클립 세트, 볼트 세트, 실링 키트 등
  - 관리 원칙: 정기 일괄 발주, 장기 커버리지 허용 (2~3개월치 일시 발주)
  - 발주 주기: 월 단위 정기 발주 (T = 30일)
  - 안전재고: z = 1.36 (서비스 수준 95%)
  - KPI 목표: 서비스 수준 95%, 재고회전율 연 6회
  - 특이사항: 대량 발주로 단가 인하 협상 가능 (MOQ 활용)


2. DEMAND_TYPE별 발주 전략
----------------------------------------------------------------

[REORDER — 소모품 정기 발주]
  대상: 오일필터, 에어필터, 스파크플러그, 드레인플러그, 전구류 등
  - 수요 패턴: 안정적, ±10% 수준의 변동
  - 발주 전략: MRP(자재소요계획) 기반 정기 발주
  - 계절 조정: 봄·가을 정기점검 시즌(3월, 9월) 수요 약 20% 증가 → 선행 발주
  - 안전재고: 표준 공식 적용

[SEASONAL — 계절성 수요 부품]
  대상: 라디에이터, 워터펌프, 쿨런트 호스, 에어컨 필터 (여름), 배터리 팩, 와이퍼 (겨울)
  - 수요 패턴: 계절에 따라 최대 1.8배 변동
  - 발주 전략: 성수기 2개월 전 선발주 (계절 선행 재고 확보)
      * 냉각계: 4월 말 기준 여름 재고 확보 완료
      * 동계 부품: 10월 말 기준 겨울 재고 확보 완료
  - 안전재고: 성수기에는 SS를 1.3배 상향 조정
  - 비수기 재고 처리: 딜러 네트워크 이관 또는 할인 프로모션 적용

[INTERMITTENT — 간헐 수요 부품]
  대상: 엔진블록, 트랜스미션 어셈블리, ECU 제어모듈, 에어백 어셈블리 등 A급 고가 부품
  - 수요 패턴: 월별 수요 발생 빈도 약 40% (60% 월은 수요 0)
  - 발주 전략: Croston 방법론 적용
      * 수요 발생 간격의 평균(α̂) 및 수요 크기의 평균(v̂)을 각각 지수평활로 추정
      * 예측 수요율 = v̂ / α̂
      * 안전재고 = v̂ × (1/α̂) × z × CV  (CV: 변동계수)
  - 실무 적용:
      * 최소 3개월 선행 발주로 장기 재고 확보
      * 긴급 발주 시 공급업체와 우선 납품 협약 (SLA) 체결
      * AS전용 부품은 전국 AS센터 분산 비축

[KIT — 세트 수요 부품]
  대상: 인젝터 세트, 실링 키트, 개스킷 (주부품과 묶음 교체)
  - 수요 패턴: 주부품(엔진블록, 트랜스미션 등) 수요와 연동하여 발생
  - 발주 전략: 주부품 발주 시 키트 구성 부품 동시 발주 (분리 발주 금지)
  - 재고 관리: 키트 단위로 관리, 구성 부품 개별 소진 금지
  - 주의사항: 키트 구성 부품 중 1종이라도 재고 부족 시 전체 키트 결품 처리


3. AS수요 vs 정비수요 구분
----------------------------------------------------------------

[AS수요 (사고/고장 대응)]
  - 특성: 예측 불가, 긴급성 높음, 지역별 랜덤 발생
  - 발주: 긴급 발주(EMERGENCY ORDER) 허용
      * 익일 납품 조건 (항공/퀵 배송 활용)
      * 프리미엄 비용 수용 (표준가 대비 최대 1.5배)
  - 재고 위치: 전국 직영AS센터(WH006) 및 딜러창고(WH007) 우선 비축
  - AS센터 안전재고: 일반 창고 대비 1.5배 유지 원칙

[정비수요 (예방정비 스케줄)]
  - 특성: 예측 가능, 차량 주행거리·정기 점검 주기 기반
  - 발주: 정기 계획 발주 (REGULAR/BLANKET ORDER)
  - 주요 정기점검 시즌: 3월(봄), 9월(가을) → 해당 월 수요 약 20% 증가
  - 예측 정확도 목표: MAPE 15% 이하


4. 재고 위험 등급 (STOCK_STATUS)
----------------------------------------------------------------

  STOCKOUT  : 현재고 = 0
              → 생산라인 중단 또는 AS 불가 위기. 즉시 긴급 발주 실행.
              → 공급업체 우선 납품 SLA 발동, 타 창고 긴급 이송 검토.

  CRITICAL  : 0 < 현재고 < 안전재고(SS)
              → 재고 위험 수준. 즉시 발주 실행.
              → 일일 모니터링 체계 전환, 상위 결재자 보고.

  LOW       : 안전재고 ≤ 현재고 < 재주문점(ROP)
              → 발주 앞당김 (표준 발주 주기 단축).
              → 수요 급증 이벤트(리콜, 캠페인 등) 모니터링.

  NORMAL    : 재주문점 ≤ 현재고 < 재주문점 × 2.5
              → 정상 재고 수준. 표준 정기 발주 유지.

  OVERSTOCK : 현재고 ≥ 재주문점 × 2.5
              → 과잉 재고. 자금 효율 저하.
              → 프로모션 판매, 타 창고 이관, 발주 일시 중단 검토.
              → 장기 과잉재고(6개월 이상)는 불용재고로 분류 후 처리.


5. 공급업체 리드타임 관리
----------------------------------------------------------------

[국내(KR) 공급업체]  현대모비스, 만도, 한국델파이, 광주솔루션
  - 평균 리드타임: 4~7일
  - 납기 신뢰도: 96~98%
  - 긴급 발주 가능: 1~2일 익일 납품 가능
  - 지연 패턴: 정시납품 90%, 경미한 지연(1~3일) 8%, 심각 지연 2%

[일본/독일(JP/DE) 공급업체]  덴소, 아이신, 보쉬, 콘티넨탈
  - 평균 리드타임: 18~22일 (해상운송 기준)
  - 납기 신뢰도: 93~95%
  - 지연 패턴: 정시납품 70%, 단기 지연(5~10일) 20%, 장기 지연(10~15일) 10%
  - 항공 긴급 발주: 7~10일 (비용 3~5배 프리미엄)
  - 관리 포인트: 해상 운송 중 기상 지연, 통관 지연 상시 모니터링

[중국(CN) 공급업체]  닝보오토파츠, 상해정밀부품공사
  - 평균 리드타임: 28~35일
  - 납기 신뢰도: 85~88%
  - 지연 패턴: 정시납품 55%, 단기 지연(7~15일) 25%, 장기 지연(15~30일) 20%
  - 관리 포인트:
      * 중국 공휴일(춘절, 국경절) 전후 3~4주 납기 추가 리드타임 필수 산정
      * 최소 2개사 이중 소싱(Dual Sourcing) 원칙
      * 공급 위험 헷지를 위한 안전재고 1.3배 상향 운용


6. KPI 정의 및 목표
----------------------------------------------------------------

[재고 서비스 수준 (Fill Rate)]
  - A급 부품: 99% 이상  (주문 대비 즉시 출고 가능 비율)
  - B급 부품: 97% 이상
  - C급 부품: 95% 이상
  - AS 부품 가용률: 98% 이상 (24시간 내 출고 보장)

[재고 회전율 (Inventory Turnover Rate, ITR)]
  - 공식: 연간 출고 수량 합계 ÷ 평균 재고 수량
  - A급: 연간 목표 12회 이상
  - B급: 연간 목표 8회 이상
  - C급: 연간 목표 6회 이상

[공급업체 납기 준수율 (OTD, On-Time Delivery)]
  - 전체 목표: 95% 이상
  - 국내 공급업체: 97% 이상
  - 해외 공급업체: 93% 이상
  - 측정 방법: (약정일 기준 납품 건수 ÷ 전체 발주 건수) × 100

[예측 정확도 (MAPE, Mean Absolute Percentage Error)]
  - 공식: (1/n) × Σ |실수요 - 예측수요| / 실수요 × 100
  - 목표: A급 10% 이하, B급 15% 이하, C급 20% 이하
  - NULL 예측은 분모에서 제외 (데이터 품질 이슈로 별도 관리)

[재고 금액 대비 결품 손실]
  - STOCKOUT 발생 시 생산 중단 비용: 시간당 약 5천만원 (완성차 라인 기준)
  - AS 결품 시 고객 불만족 비용: 건당 30~50만원 추정
  - 목표: 연간 STOCKOUT 발생 건수 전년 대비 20% 감소


7. 테이블 간 주요 JOIN 패턴
----------------------------------------------------------------

[① ABC 등급별 재고 현황 분석]
  SELECT p.PART_CLASS, p.PART_NAME, i.STOCK_STATUS, i.INVENTORY_VALUE_KRW
  FROM FACT_INVENTORY i
  JOIN MST_PART p ON i.PART_ID = p.PART_ID
  WHERE i.SNAPSHOT_DATE = '2024-12-31'
  ORDER BY p.PART_CLASS, i.STOCK_STATUS

[② 공급업체별 납기 준수율 분석]
  SELECT s.SUPPLIER_NAME, s.COUNTRY,
         COUNT(*) AS 전체발주,
         SUM(CASE WHEN o.STATUS = 'DELIVERED' AND o.DELAY_DAYS = 0 THEN 1 ELSE 0 END) AS 정시납품,
         ROUND(100.0 * SUM(CASE WHEN o.DELAY_DAYS = 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS OTD_PCT
  FROM FACT_ORDER o
  JOIN MST_SUPPLIER s ON o.SUPPLIER_ID = s.SUPPLIER_ID
  WHERE o.STATUS IN ('DELIVERED','DELAYED','PARTIAL')
  GROUP BY s.SUPPLIER_NAME, s.COUNTRY

[③ 부품별 예측 오차율 분석 (MAPE 계산)]
  SELECT p.PART_NAME, p.PART_CLASS, p.DEMAND_TYPE,
         AVG(d.FORECAST_ERROR_PCT) AS MAPE
  FROM FACT_MONTHLY_DEMAND d
  JOIN MST_PART p ON d.PART_ID = p.PART_ID
  WHERE d.FORECAST_QTY IS NOT NULL
  GROUP BY p.PART_NAME, p.PART_CLASS, p.DEMAND_TYPE
  ORDER BY MAPE DESC

[④ 재고 커버리지 (재고 ÷ 일평균수요)]
  SELECT i.PART_ID, i.WAREHOUSE_ID, i.SNAPSHOT_DATE,
         i.STOCK_QTY,
         ROUND(d.DEMAND_QTY / 30.0, 2) AS 일평균수요,
         ROUND(i.STOCK_QTY / (d.DEMAND_QTY / 30.0), 1) AS 커버리지_일수
  FROM FACT_INVENTORY i
  JOIN FACT_MONTHLY_DEMAND d
    ON i.PART_ID = d.PART_ID
   AND i.WAREHOUSE_ID = d.WAREHOUSE_ID
   AND SUBSTR(i.SNAPSHOT_DATE, 1, 7) = d.YEAR_MONTH
  WHERE d.DEMAND_QTY > 0

[⑤ CRITICAL/STOCKOUT 부품의 발주 이력 확인]
  SELECT i.PART_ID, p.PART_NAME, i.WAREHOUSE_ID, i.STOCK_STATUS,
         o.ORDER_DATE, o.STATUS AS 발주상태, o.DELAY_DAYS
  FROM FACT_INVENTORY i
  JOIN MST_PART p ON i.PART_ID = p.PART_ID
  LEFT JOIN FACT_ORDER o ON i.PART_ID = o.PART_ID AND i.WAREHOUSE_ID = o.WAREHOUSE_ID
  WHERE i.STOCK_STATUS IN ('CRITICAL','STOCKOUT')
    AND i.SNAPSHOT_DATE = '2024-12-31'
  ORDER BY i.STOCK_STATUS, o.ORDER_DATE DESC


8. 데이터 범위 및 특이사항
----------------------------------------------------------------

  기간:       2022년 1월 ~ 2024년 12월 (3년, 36개월)
  부품 수:    30종 (A급 10종, B급 12종, C급 8종)
  공급업체:   10개 (국내 4개, 일본 2개, 독일 2개, 중국 2개)
  창고/거점:  8개 (중앙물류 2, 지역창고 3, AS센터 1, 딜러창고 1, 해외 1)

  수요 레코드: 부품-창고 적용 조합 × 36개월 (약 6,000~8,000행)
    - INTERMITTENT 부품은 약 60% 월이 수요=0
    - 예측 NULL 약 20% (현실적 데이터 품질 반영)

  재고 스냅샷: 분기말 × 부품-창고 조합 (약 2,000~3,000행)
    - LAST_MOVEMENT_DATE NULL 약 15% (장기 미출고 부품)

  발주 이력: 약 3,000~4,000건
    - 국내 KR: 정시납품 위주 (DELAY_DAYS 0~3일)
    - 일본/독일 JP/DE: 중기 지연 가능 (DELAY_DAYS 5~15일)
    - 중국 CN: 장기 지연 리스크 (DELAY_DAYS 10~30일)
    - 취소(CANCELLED): 약 5%, 부분납품(PARTIAL): 약 8%

  [참조 무결성 보장]
    - 모든 FACT 테이블의 PART_ID → MST_PART 존재
    - 모든 FACT 테이블의 WAREHOUSE_ID → MST_WAREHOUSE 존재
    - FACT_ORDER.SUPPLIER_ID → MST_SUPPLIER 존재
    - FACT_ORDER.SUPPLIER_ID = MST_PART.SUPPLIER_ID (동일 부품-공급업체 매핑)

================================================================
"""


def write_logic_document():
    path = os.path.join(DATA_DIR, "LOGIC_DOCUMENT.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(LOGIC_DOC)
    print(f"  LOGIC_DOCUMENT.txt      - {len(LOGIC_DOC.splitlines())}줄")


# ── 실행 ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n자동차 부품 SCM 데모 데이터 생성 시작 → {DATA_DIR}/\n")

    gen_mst_supplier()
    gen_mst_warehouse()
    gen_mst_part()
    demand_map = gen_fact_monthly_demand()
    gen_fact_inventory(demand_map)
    gen_fact_order()
    write_schema_json()
    write_logic_document()

    # ── 참조 무결성 검증 ─────────────────────────────────────────────────────
    print("\n[참조 무결성 검증]")

    def load_csv(fname):
        path = os.path.join(DATA_DIR, fname)
        with open(path, encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))

    part_keys     = {r["PART_ID"]      for r in load_csv("MST_PART.csv")}
    supplier_keys = {r["SUPPLIER_ID"]  for r in load_csv("MST_SUPPLIER.csv")}
    wh_keys       = {r["WAREHOUSE_ID"] for r in load_csv("MST_WAREHOUSE.csv")}

    demand_rows = load_csv("FACT_MONTHLY_DEMAND.csv")
    inv_rows    = load_csv("FACT_INVENTORY.csv")
    order_rows  = load_csv("FACT_ORDER.csv")

    checks = [
        ("FACT_MONTHLY_DEMAND.PART_ID      → MST_PART",
         all(r["PART_ID"]      in part_keys     for r in demand_rows)),
        ("FACT_MONTHLY_DEMAND.WAREHOUSE_ID  → MST_WAREHOUSE",
         all(r["WAREHOUSE_ID"] in wh_keys       for r in demand_rows)),
        ("FACT_INVENTORY.PART_ID            → MST_PART",
         all(r["PART_ID"]      in part_keys     for r in inv_rows)),
        ("FACT_INVENTORY.WAREHOUSE_ID       → MST_WAREHOUSE",
         all(r["WAREHOUSE_ID"] in wh_keys       for r in inv_rows)),
        ("FACT_ORDER.PART_ID               → MST_PART",
         all(r["PART_ID"]      in part_keys     for r in order_rows)),
        ("FACT_ORDER.SUPPLIER_ID           → MST_SUPPLIER",
         all(r["SUPPLIER_ID"]  in supplier_keys for r in order_rows)),
        ("FACT_ORDER.WAREHOUSE_ID          → MST_WAREHOUSE",
         all(r["WAREHOUSE_ID"] in wh_keys       for r in order_rows)),
    ]

    all_ok = True
    for label, ok in checks:
        status_str = "[PASS]" if ok else "[FAIL]"
        print(f"  {status_str}  {label}")
        all_ok = all_ok and ok

    print(f"\n{'모든 참조 무결성 검증 통과!' if all_ok else '일부 검증 실패 — 위 항목 확인 필요'}")
    print(f"\n생성 완료: {DATA_DIR}/\n")
