"""
스마트팩토리 생산 관리 데모 데이터 생성기

테이블:
  - MST_LINE          : 생산 라인 마스터 (6개)
  - MST_EQUIPMENT     : 설비 마스터 (15개)
  - MST_PRODUCT       : 제품 마스터 (20개)
  - FACT_PRODUCTION   : 일별 생산 실적 (2023-01-01 ~ 2024-12-31)
  - FACT_DEFECT       : 불량 기록 (~2000건)
  - FACT_MAINTENANCE  : 정비 기록 (~800건)
  - SCHEMA_DEFINITION.json
  - LOGIC_DOCUMENT.txt
"""

import csv
import json
import os
import random
from datetime import date, timedelta

random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "manufacturing")
os.makedirs(DATA_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# HELPER
# ═══════════════════════════════════════════════════════════════

def write_csv(filename, fieldnames, rows):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows):,} rows → {filename}")


def maybe_null(value, null_prob=0.2):
    """Return None with null_prob probability, else value."""
    return None if random.random() < null_prob else value


def date_range(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


# ═══════════════════════════════════════════════════════════════
# 1. MST_LINE — 6 production lines
# ═══════════════════════════════════════════════════════════════

LINE_DATA = [
    # LINE_ID, LINE_NAME, LINE_TYPE, FACTORY_FLOOR, SHIFT_COUNT, DESIGN_CAPACITY_DAILY, STATUS, LINE_MANAGER
    ("LINE-01", "CNC가공라인",   "가공",  "A동", 3, 960,  "OPERATING",   "김철수"),
    ("LINE-02", "프레스라인",    "프레스","A동", 2, 1920, "OPERATING",   "이영희"),
    ("LINE-03", "용접라인",      "용접",  "B동", 3, 1440, "OPERATING",   "박민준"),
    ("LINE-04", "도장라인",      "도장",  "B동", 2, 480,  "OPERATING",   "최수진"),
    ("LINE-05", "조립라인",      "조립",  "C동", 3, 1200, "MAINTENANCE", "정우성"),
    ("LINE-06", "검사라인",      "검사",  "C동", 2, 3840, "OPERATING",   "강지원"),
]

LINE_FIELDS = [
    "LINE_ID", "LINE_NAME", "LINE_TYPE", "FACTORY_FLOOR",
    "SHIFT_COUNT", "DESIGN_CAPACITY_DAILY", "STATUS", "LINE_MANAGER",
]

LINE_ROWS = [dict(zip(LINE_FIELDS, row)) for row in LINE_DATA]

# quick lookup
LINE_IDS = [r["LINE_ID"] for r in LINE_ROWS]


# ═══════════════════════════════════════════════════════════════
# 2. MST_EQUIPMENT — 15 pieces of equipment
# ═══════════════════════════════════════════════════════════════

EQUIPMENT_DATA = [
    # EQP_ID, NAME,            TYPE,     LINE_ID,   MANUFACTURER,  INSTALL_DATE, CAP/HR, OEE_TGT, MAINT_DAYS, STATUS,        ASSET_KRW
    ("EQP001","CNC선반_A1",    "CNC선반", "LINE-01","현대위아",    "2018-03-15",  40, 80, 30, "OPERATING",   850000000),
    ("EQP002","CNC선반_A2",    "CNC선반", "LINE-01","현대위아",    "2018-03-15",  40, 80, 30, "OPERATING",   850000000),
    ("EQP003","프레스_B1",     "프레스",  "LINE-02","고려프레스",  "2019-06-20",  120,75, 60, "OPERATING",   1200000000),
    ("EQP004","용접로봇_C1",   "용접로봇","LINE-03","현대로보틱스","2020-01-10",  60, 82, 30, "OPERATING",   950000000),
    ("EQP005","용접로봇_C2",   "용접로봇","LINE-03","현대로보틱스","2020-01-10",  60, 82, 30, "OPERATING",   950000000),
    ("EQP006","도장설비_D1",   "도장설비","LINE-04","SPX",         "2017-09-05",  30, 78, 60, "OPERATING",   1500000000),
    ("EQP007","조립로봇_E1",   "조립로봇","LINE-05","FANUC",       "2021-04-22",  50, 85, 30, "MAINTENANCE", 780000000),
    ("EQP008","조립로봇_E2",   "조립로봇","LINE-05","FANUC",       "2021-04-22",  50, 85, 30, "OPERATING",   780000000),
    ("EQP009","검사장비_F1",   "검사장비","LINE-06","Keyence",     "2022-02-14",  200,83, 90, "OPERATING",   320000000),
    ("EQP010","컨베이어_G1",   "컨베이어","LINE-01","동일체인",    "2016-11-30",  500,77, 90, "OPERATING",   180000000),
    ("EQP011","CNC밀링_A3",    "CNC선반", "LINE-01","DMG",         "2020-07-08",  35, 80, 30, "OPERATING",   920000000),
    ("EQP012","스폿용접_C3",   "용접로봇","LINE-03","ABB",         "2019-12-01",  80, 82, 30, "OPERATING",   1050000000),
    ("EQP013","프레스_B2",     "프레스",  "LINE-02","고려프레스",  "2021-03-18",  100,75, 60, "OPERATING",   1100000000),
    ("EQP014","조립로봇_E3",   "조립로봇","LINE-05","FANUC",       "2022-08-25",  45, 85, 30, "BREAKDOWN",   750000000),
    ("EQP015","검사장비_F2",   "검사장비","LINE-06","Cognex",      "2023-01-09",  180,83, 90, "OPERATING",   290000000),
]

EQUIPMENT_FIELDS = [
    "EQUIPMENT_ID", "EQUIPMENT_NAME", "EQUIPMENT_TYPE", "LINE_ID",
    "MANUFACTURER", "INSTALL_DATE", "DESIGN_CAPACITY_PER_HOUR",
    "OEE_TARGET_PCT", "MAINTENANCE_CYCLE_DAYS", "STATUS", "ASSET_VALUE_KRW",
]

EQUIPMENT_ROWS = [dict(zip(EQUIPMENT_FIELDS, row)) for row in EQUIPMENT_DATA]

EQP_IDS      = [r["EQUIPMENT_ID"] for r in EQUIPMENT_ROWS]
EQP_BY_LINE  = {}  # LINE_ID → list of EQUIPMENT_IDs
for r in EQUIPMENT_ROWS:
    EQP_BY_LINE.setdefault(r["LINE_ID"], []).append(r["EQUIPMENT_ID"])


# ═══════════════════════════════════════════════════════════════
# 3. MST_PRODUCT — 20 products
# ═══════════════════════════════════════════════════════════════

PRODUCT_DATA = [
    # PRD_ID, NAME,                   TYPE,  CATEGORY,   LINE_ID,    CYCLE_SEC, STD_COST,    DEMAND_TYPE,       TGT_DAILY, DEFECT_THR, LAUNCH,        STATUS
    ("PRD001","엔진블록_V6",          "완성품","엔진부품","LINE-01",  90,  450000, "MASS_PRODUCTION", 320, 1.0, "2020-01-01","ACTIVE"),
    ("PRD002","크랭크샤프트",         "반제품","엔진부품","LINE-01",  120, 280000, "MASS_PRODUCTION", 240, 1.5, "2020-01-01","ACTIVE"),
    ("PRD003","실린더헤드",           "반제품","엔진부품","LINE-01",  80,  190000, "MASS_PRODUCTION", 360, 1.2, "2021-03-01","ACTIVE"),
    ("PRD004","도어패널_좌",          "반제품","차체부품","LINE-02",  30,  85000,  "MASS_PRODUCTION", 800, 0.8, "2019-06-01","ACTIVE"),
    ("PRD005","도어패널_우",          "반제품","차체부품","LINE-02",  30,  85000,  "MASS_PRODUCTION", 800, 0.8, "2019-06-01","ACTIVE"),
    ("PRD006","후드패널",             "반제품","차체부품","LINE-02",  45,  120000, "MASS_PRODUCTION", 600, 1.0, "2019-06-01","ACTIVE"),
    ("PRD007","머플러_조립체",        "완성품","엔진부품","LINE-03",  60,  95000,  "MASS_PRODUCTION", 480, 1.5, "2020-09-01","ACTIVE"),
    ("PRD008","차체프레임_용접",      "반제품","차체부품","LINE-03",  180, 320000, "SMALL_BATCH",     160, 2.0, "2021-01-01","ACTIVE"),
    ("PRD009","연료탱크",             "완성품","안전부품","LINE-03",  90,  145000, "MASS_PRODUCTION", 320, 0.5, "2020-01-01","ACTIVE"),
    ("PRD010","범퍼빔",               "부품",  "차체부품","LINE-03",  40,  62000,  "MASS_PRODUCTION", 720, 1.0, "2022-04-01","ACTIVE"),
    ("PRD011","외장패널_도장",        "반제품","차체부품","LINE-04",  300, 75000,  "MASS_PRODUCTION", 96,  1.5, "2019-01-01","ACTIVE"),
    ("PRD012","플라스틱커버_도장",    "부품",  "인테리어","LINE-04",  240, 42000,  "SMALL_BATCH",     120, 2.0, "2020-06-01","ACTIVE"),
    ("PRD013","대시보드_조립",        "완성품","인테리어","LINE-05",  600, 380000, "MASS_PRODUCTION", 72,  1.0, "2021-05-01","ACTIVE"),
    ("PRD014","시트프레임",           "반제품","인테리어","LINE-05",  480, 210000, "MASS_PRODUCTION", 90,  1.5, "2021-05-01","ACTIVE"),
    ("PRD015","에어백모듈",           "완성품","안전부품","LINE-05",  360, 520000, "MASS_PRODUCTION", 120, 0.5, "2022-01-01","ACTIVE"),
    ("PRD016","ABS브레이크모듈",      "완성품","안전부품","LINE-05",  420, 680000, "SMALL_BATCH",     60,  0.5, "2022-07-01","ACTIVE"),
    ("PRD017","ECU_전장모듈",         "완성품","전장부품","LINE-06",  180, 950000, "CUSTOM",          40,  0.5, "2023-01-01","ACTIVE"),
    ("PRD018","와이어링하네스",       "부품",  "전장부품","LINE-06",  120, 145000, "MASS_PRODUCTION", 200, 1.0, "2020-03-01","ACTIVE"),
    ("PRD019","레거시엔진_구형",      "완성품","엔진부품","LINE-01",  110, 380000, "DISCONTINUE",     80,  3.0, "2017-01-01","EOL"),
    ("PRD020","구형도어패널",         "반제품","차체부품","LINE-02",  35,  72000,  "DISCONTINUE",     100, 2.5, "2016-01-01","EOL"),
]

PRODUCT_FIELDS = [
    "PRODUCT_ID", "PRODUCT_NAME", "PRODUCT_TYPE", "CATEGORY",
    "LINE_ID", "CYCLE_TIME_SECONDS", "STANDARD_COST_KRW",
    "DEMAND_TYPE", "TARGET_DAILY_OUTPUT", "DEFECT_THRESHOLD_PCT",
    "LAUNCH_DATE", "STATUS",
]

PRODUCT_ROWS = [dict(zip(PRODUCT_FIELDS, row)) for row in PRODUCT_DATA]

# LINE_ID → list of PRODUCT_IDs
PRODUCTS_BY_LINE = {}
for r in PRODUCT_ROWS:
    PRODUCTS_BY_LINE.setdefault(r["LINE_ID"], []).append(r["PRODUCT_ID"])

# quick lookup dict
PRODUCT_MAP = {r["PRODUCT_ID"]: r for r in PRODUCT_ROWS}


# ═══════════════════════════════════════════════════════════════
# 4. FACT_PRODUCTION — daily 2023-01-01 ~ 2024-12-31
# ═══════════════════════════════════════════════════════════════

DOWNTIME_REASONS = ["설비고장", "원자재부족", "품질문제", "계획정비", "라인전환"]

def seasonal_factor(d: date) -> float:
    """Slightly lower in Jan (holiday) and Aug (summer shutdown)."""
    if d.month == 1:
        return 0.88
    if d.month == 8:
        return 0.92
    return 1.0


def generate_production():
    rows = []
    prod_id_counter = 1

    start = date(2023, 1, 1)
    end   = date(2024, 12, 31)
    all_dates = list(date_range(start, end))

    # track current product per line to detect changeovers
    line_current_product = {}
    # track maintenance day count per line per month to limit to 1-3/month
    line_maint_days = {}  # (LINE_ID, year, month) → count

    for line in LINE_ROWS:
        lid = line["LINE_ID"]
        design_cap = line["DESIGN_CAPACITY_DAILY"]
        prods = PRODUCTS_BY_LINE.get(lid, ["PRD001"])

        current_product = prods[0]
        line_current_product[lid] = current_product
        # switch product every ~90 days
        last_switch = start

        for d in all_dates:
            year, month = d.year, d.month
            maint_key = (lid, year, month)

            # maybe switch product ~every 60-120 days
            if (d - last_switch).days >= random.randint(60, 120) and len(prods) > 1:
                new_prod = random.choice([p for p in prods if p != current_product])
                current_product = new_prod
                line_current_product[lid] = current_product
                last_switch = d
                changeover = True
            else:
                changeover = False

            season = seasonal_factor(d)

            # Decide day type
            maint_count = line_maint_days.get(maint_key, 0)
            # planned maintenance: 1-3 times/month, but only if not already at max
            is_maintenance = False
            if maint_count < random.randint(1, 3):
                # roughly 1 maintenance day per ~10 work days
                if random.random() < 0.10:
                    is_maintenance = True
                    line_maint_days[maint_key] = maint_count + 1

            is_breakdown = (not is_maintenance) and (random.random() < 0.05)

            # PLANNED OUTPUT based on design capacity
            planned = int(design_cap * random.uniform(0.80, 0.95))

            if is_maintenance:
                util = random.uniform(0.0, 0.30)
                actual = int(planned * util)
                shift = "주간"
                op_hours = round(random.uniform(2, 6), 1)
                downtime_hours = round(24 - op_hours - random.uniform(0, 2), 1)
                downtime_reason = "계획정비"
            elif is_breakdown:
                util = random.uniform(0.0, 0.60)
                actual = int(planned * util)
                shift = random.choice(["주간", "야간", "전일"])
                op_hours = round(random.uniform(4, 18), 1)
                downtime_hours = round(24 - op_hours - random.uniform(0, 2), 1)
                downtime_reason = "설비고장"
            else:
                noise = random.uniform(0.85, 1.05) * season
                if changeover:
                    noise *= random.uniform(0.80, 0.92)
                actual = int(planned * noise)
                util = round(actual / planned * 100, 1) if planned else 0
                shift_choices = ["전일"] if line["SHIFT_COUNT"] == 3 else ["주간", "야간"]
                shift = random.choice(shift_choices)
                op_hours = round(random.uniform(20, 24), 1)

                # downtime only when changeover or random small event
                if changeover:
                    downtime_hours = round(random.uniform(2, 4), 1)
                    downtime_reason = "라인전환"
                elif random.random() < 0.15:
                    downtime_hours = round(random.uniform(0.5, 3), 1)
                    downtime_reason = random.choice(DOWNTIME_REASONS)
                else:
                    downtime_hours = None   # ~70% have no downtime
                    downtime_reason = None

            util = round(actual / planned * 100, 1) if planned else 0.0
            yield_rate = round(random.uniform(96, 99.5), 2) if not is_breakdown else round(random.uniform(88, 97), 2)

            # ~10% chance to nullify downtime_hours even if it exists
            if downtime_hours is not None and random.random() < 0.10:
                downtime_hours = None
                downtime_reason = None

            rows.append({
                "PRODUCTION_ID":       f"PRD-{prod_id_counter:06d}",
                "LINE_ID":             lid,
                "PRODUCT_ID":          current_product,
                "PRODUCTION_DATE":     d.isoformat(),
                "SHIFT":               shift,
                "PLANNED_OUTPUT":      planned,
                "ACTUAL_OUTPUT":       actual,
                "UTILIZATION_RATE_PCT":util,
                "OPERATION_HOURS":     op_hours,
                "DOWNTIME_HOURS":      downtime_hours,
                "DOWNTIME_REASON":     downtime_reason,
                "YIELD_RATE_PCT":      yield_rate,
            })
            prod_id_counter += 1

    return rows


PRODUCTION_FIELDS = [
    "PRODUCTION_ID", "LINE_ID", "PRODUCT_ID", "PRODUCTION_DATE",
    "SHIFT", "PLANNED_OUTPUT", "ACTUAL_OUTPUT", "UTILIZATION_RATE_PCT",
    "OPERATION_HOURS", "DOWNTIME_HOURS", "DOWNTIME_REASON", "YIELD_RATE_PCT",
]


# ═══════════════════════════════════════════════════════════════
# 5. FACT_DEFECT — ~2000 defect records 2023-2024
# ═══════════════════════════════════════════════════════════════

DEFECT_TYPES_BY_LINE = {
    "LINE-01": ["치수불량", "외관불량", "기능불량"],
    "LINE-02": ["치수불량", "외관불량"],
    "LINE-03": ["용접불량", "치수불량", "기능불량"],
    "LINE-04": ["도장불량", "외관불량"],
    "LINE-05": ["조립불량", "기능불량", "외관불량"],
    "LINE-06": ["치수불량", "기능불량", "외관불량"],
}

ROOT_CAUSES = ["설비마모", "원자재불량", "작업자오류", "공정파라미터", "환경요인"]
DISPOSITIONS = ["재작업", "폐기", "특채"]

SEVERITY_WEIGHTS = ["CRITICAL"] * 10 + ["MAJOR"] * 40 + ["MINOR"] * 50  # 10/40/50


def generate_defects():
    rows = []
    start = date(2023, 1, 1)
    end   = date(2024, 12, 31)
    all_dates = list(date_range(start, end))

    target = 2000
    for i in range(1, target + 1):
        d = random.choice(all_dates)
        line = random.choice(LINE_ROWS)
        lid = line["LINE_ID"]

        eqp_list = EQP_BY_LINE.get(lid, EQP_IDS[:1])
        eqp_id = random.choice(eqp_list)

        prod_list = PRODUCTS_BY_LINE.get(lid, ["PRD001"])
        prd_id = random.choice(prod_list)

        defect_type = random.choice(DEFECT_TYPES_BY_LINE.get(lid, ["치수불량"]))
        severity    = random.choice(SEVERITY_WEIGHTS)

        # inspected qty
        inspected = random.randint(50, 500)

        # spike during equipment problems (random ~10% of records)
        if random.random() < 0.10:
            defect_rate = round(random.uniform(5.0, 10.0), 2)
        else:
            defect_rate = round(random.uniform(0.5, 2.0), 2)

        defect_qty = max(1, int(inspected * defect_rate / 100))
        actual_rate = round(defect_qty / inspected * 100, 2)

        disposition = random.choice(DISPOSITIONS)

        # rework cost only when disposition is 재작업 (and ~70% of those)
        if disposition == "재작업" and random.random() > 0.30:
            rework_cost = random.randint(50000, 2000000)
        else:
            rework_cost = None

        root_cause = maybe_null(random.choice(ROOT_CAUSES), null_prob=0.20)

        rows.append({
            "DEFECT_ID":        f"DFT-{i:06d}",
            "LINE_ID":          lid,
            "EQUIPMENT_ID":     eqp_id,
            "PRODUCT_ID":       prd_id,
            "DEFECT_DATE":      d.isoformat(),
            "DEFECT_TYPE":      defect_type,
            "INSPECTED_QTY":    inspected,
            "DEFECT_QTY":       defect_qty,
            "DEFECT_RATE_PCT":  actual_rate,
            "SEVERITY":         severity,
            "DISPOSITION":      disposition,
            "REWORK_COST_KRW":  rework_cost,
            "ROOT_CAUSE":       root_cause,
        })

    return rows


DEFECT_FIELDS = [
    "DEFECT_ID", "LINE_ID", "EQUIPMENT_ID", "PRODUCT_ID", "DEFECT_DATE",
    "DEFECT_TYPE", "INSPECTED_QTY", "DEFECT_QTY", "DEFECT_RATE_PCT",
    "SEVERITY", "DISPOSITION", "REWORK_COST_KRW", "ROOT_CAUSE",
]


# ═══════════════════════════════════════════════════════════════
# 6. FACT_MAINTENANCE — ~800 records 2022-2024
# ═══════════════════════════════════════════════════════════════

MAINTENANCE_TYPES = ["예방정비", "사후정비", "개량정비", "긴급정비"]
# 60% PM, 25% corrective, 15% emergency → use weighted list
MAINT_TYPE_WEIGHTS = (
    ["예방정비"] * 60 + ["사후정비"] * 25 + ["긴급정비"] * 10 + ["개량정비"] * 5
)

TECHNICIANS = [f"TECH{i:03d}" for i in range(1, 11)]

RESULT_NOTES = [
    "정상 완료", "부품 교체 완료", "교정 완료", "오일 교환 완료",
    "센서 교체", "벨트 교체", "필터 청소", "축 정렬 완료",
    None, None,  # ~20% NULL built in
]


def generate_maintenance():
    rows = []
    start = date(2022, 1, 1)
    end   = date(2024, 12, 31)
    all_dates = list(date_range(start, end))

    target = 800
    for i in range(1, target + 1):
        d = random.choice(all_dates)
        eqp = random.choice(EQUIPMENT_ROWS)
        eqp_id = eqp["EQUIPMENT_ID"]
        cycle_days = eqp["MAINTENANCE_CYCLE_DAYS"]

        maint_type = random.choice(MAINT_TYPE_WEIGHTS)

        # SCHEDULED vs completed
        if random.random() < 0.08:
            status = "SCHEDULED"
        elif random.random() < 0.04:
            status = "IN_PROGRESS"
        else:
            status = "COMPLETED"

        planned_hours = round(random.uniform(2, 16), 1)

        if status == "SCHEDULED":
            actual_hours = None
            total_cost   = None
        else:
            actual_hours = round(planned_hours * random.uniform(0.8, 1.4), 1)
            total_cost   = None  # computed below

        technician = random.choice(TECHNICIANS)

        # parts cost: NULL ~15%
        if status == "SCHEDULED" or random.random() < 0.15:
            parts_cost = None
        else:
            parts_cost = random.randint(50000, 5000000)

        labor_cost = round(actual_hours * random.randint(30000, 60000), -3) if actual_hours else None

        if parts_cost is not None and labor_cost is not None:
            total_cost = parts_cost + labor_cost
        else:
            total_cost = None

        next_maint = (d + timedelta(days=cycle_days)).isoformat()
        downtime_h = round(random.uniform(0.5, actual_hours if actual_hours else planned_hours), 1)

        result_note = maybe_null(random.choice([n for n in RESULT_NOTES if n is not None]), null_prob=0.20)

        rows.append({
            "MAINTENANCE_ID":      f"MNT-{i:06d}",
            "EQUIPMENT_ID":        eqp_id,
            "MAINTENANCE_DATE":    d.isoformat(),
            "MAINTENANCE_TYPE":    maint_type,
            "STATUS":              status,
            "PLANNED_HOURS":       planned_hours,
            "ACTUAL_HOURS":        actual_hours,
            "TECHNICIAN_ID":       technician,
            "PARTS_COST_KRW":      parts_cost,
            "LABOR_COST_KRW":      labor_cost,
            "TOTAL_COST_KRW":      total_cost,
            "NEXT_MAINTENANCE_DATE": next_maint,
            "DOWNTIME_HOURS":      downtime_h,
            "RESULT_NOTE":         result_note,
        })

    return rows


MAINTENANCE_FIELDS = [
    "MAINTENANCE_ID", "EQUIPMENT_ID", "MAINTENANCE_DATE", "MAINTENANCE_TYPE",
    "STATUS", "PLANNED_HOURS", "ACTUAL_HOURS", "TECHNICIAN_ID",
    "PARTS_COST_KRW", "LABOR_COST_KRW", "TOTAL_COST_KRW",
    "NEXT_MAINTENANCE_DATE", "DOWNTIME_HOURS", "RESULT_NOTE",
]


# ═══════════════════════════════════════════════════════════════
# 7. SCHEMA_DEFINITION.json
# ═══════════════════════════════════════════════════════════════

SCHEMA = {
    "database": "manufacturing_demo",
    "description": "스마트팩토리 생산 관리 데모 데이터셋",
    "tables": {
        "MST_LINE": {
            "description": "생산 라인 마스터",
            "primary_key": "LINE_ID",
            "columns": {
                "LINE_ID":               {"type": "VARCHAR(10)",  "nullable": False, "description": "라인 고유 ID"},
                "LINE_NAME":             {"type": "VARCHAR(30)",  "nullable": False, "description": "라인 이름"},
                "LINE_TYPE":             {"type": "VARCHAR(10)",  "nullable": False, "description": "라인 유형 (가공/프레스/용접/도장/조립/검사)"},
                "FACTORY_FLOOR":         {"type": "VARCHAR(5)",   "nullable": False, "description": "공장 동 (A동/B동/C동)"},
                "SHIFT_COUNT":           {"type": "INT",          "nullable": False, "description": "교대 횟수 (1/2/3)"},
                "DESIGN_CAPACITY_DAILY": {"type": "INT",          "nullable": False, "description": "일 설계 생산 능력 (개)"},
                "STATUS":                {"type": "VARCHAR(15)",  "nullable": False, "description": "운영 상태 (OPERATING/MAINTENANCE/SETUP)"},
                "LINE_MANAGER":          {"type": "VARCHAR(20)",  "nullable": False, "description": "라인 담당자"},
            },
        },
        "MST_EQUIPMENT": {
            "description": "설비 마스터",
            "primary_key": "EQUIPMENT_ID",
            "foreign_keys": {"LINE_ID": "MST_LINE.LINE_ID"},
            "columns": {
                "EQUIPMENT_ID":              {"type": "VARCHAR(10)",  "nullable": False},
                "EQUIPMENT_NAME":            {"type": "VARCHAR(30)",  "nullable": False},
                "EQUIPMENT_TYPE":            {"type": "VARCHAR(15)",  "nullable": False, "description": "CNC선반/프레스/용접로봇/도장설비/검사장비/조립로봇/컨베이어"},
                "LINE_ID":                   {"type": "VARCHAR(10)",  "nullable": False, "fk": "MST_LINE.LINE_ID"},
                "MANUFACTURER":              {"type": "VARCHAR(30)",  "nullable": False},
                "INSTALL_DATE":              {"type": "DATE",         "nullable": False},
                "DESIGN_CAPACITY_PER_HOUR":  {"type": "INT",          "nullable": False, "description": "시간당 설계 생산량"},
                "OEE_TARGET_PCT":            {"type": "DECIMAL(5,2)", "nullable": False, "description": "OEE 목표 (%)"},
                "MAINTENANCE_CYCLE_DAYS":    {"type": "INT",          "nullable": False, "description": "예방정비 주기 (일)"},
                "STATUS":                    {"type": "VARCHAR(15)",  "nullable": False, "description": "OPERATING/MAINTENANCE/BREAKDOWN/STANDBY"},
                "ASSET_VALUE_KRW":           {"type": "BIGINT",       "nullable": False, "description": "자산가치 (원)"},
            },
        },
        "MST_PRODUCT": {
            "description": "제품 마스터",
            "primary_key": "PRODUCT_ID",
            "foreign_keys": {"LINE_ID": "MST_LINE.LINE_ID"},
            "columns": {
                "PRODUCT_ID":          {"type": "VARCHAR(10)",  "nullable": False},
                "PRODUCT_NAME":        {"type": "VARCHAR(40)",  "nullable": False},
                "PRODUCT_TYPE":        {"type": "VARCHAR(10)",  "nullable": False, "description": "완성품/반제품/부품"},
                "CATEGORY":            {"type": "VARCHAR(15)",  "nullable": False, "description": "엔진부품/차체부품/전장부품/인테리어/안전부품"},
                "LINE_ID":             {"type": "VARCHAR(10)",  "nullable": False, "fk": "MST_LINE.LINE_ID"},
                "CYCLE_TIME_SECONDS":  {"type": "INT",          "nullable": False, "description": "개당 사이클 타임 (초)"},
                "STANDARD_COST_KRW":   {"type": "INT",          "nullable": False},
                "DEMAND_TYPE":         {"type": "VARCHAR(20)",  "nullable": False, "description": "MASS_PRODUCTION/SMALL_BATCH/CUSTOM/DISCONTINUE"},
                "TARGET_DAILY_OUTPUT": {"type": "INT",          "nullable": False},
                "DEFECT_THRESHOLD_PCT":{"type": "DECIMAL(4,2)", "nullable": False, "description": "허용 불량률 (%)"},
                "LAUNCH_DATE":         {"type": "DATE",         "nullable": False},
                "STATUS":              {"type": "VARCHAR(10)",  "nullable": False, "description": "ACTIVE/EOL"},
            },
        },
        "FACT_PRODUCTION": {
            "description": "일별 생산 실적 (2023-01-01 ~ 2024-12-31)",
            "primary_key": "PRODUCTION_ID",
            "foreign_keys": {
                "LINE_ID":    "MST_LINE.LINE_ID",
                "PRODUCT_ID": "MST_PRODUCT.PRODUCT_ID",
            },
            "columns": {
                "PRODUCTION_ID":       {"type": "VARCHAR(15)",  "nullable": False},
                "LINE_ID":             {"type": "VARCHAR(10)",  "nullable": False},
                "PRODUCT_ID":          {"type": "VARCHAR(10)",  "nullable": False},
                "PRODUCTION_DATE":     {"type": "DATE",         "nullable": False},
                "SHIFT":               {"type": "VARCHAR(5)",   "nullable": False, "description": "주간/야간/전일"},
                "PLANNED_OUTPUT":      {"type": "INT",          "nullable": False},
                "ACTUAL_OUTPUT":       {"type": "INT",          "nullable": False},
                "UTILIZATION_RATE_PCT":{"type": "DECIMAL(5,2)", "nullable": False},
                "OPERATION_HOURS":     {"type": "DECIMAL(4,1)", "nullable": False},
                "DOWNTIME_HOURS":      {"type": "DECIMAL(4,1)", "nullable": True,  "description": "비가동 시간 (NULL = 비가동 없음)"},
                "DOWNTIME_REASON":     {"type": "VARCHAR(20)",  "nullable": True,  "description": "설비고장/원자재부족/품질문제/계획정비/라인전환"},
                "YIELD_RATE_PCT":      {"type": "DECIMAL(5,2)", "nullable": False},
            },
        },
        "FACT_DEFECT": {
            "description": "불량 기록 (2023-2024)",
            "primary_key": "DEFECT_ID",
            "foreign_keys": {
                "LINE_ID":      "MST_LINE.LINE_ID",
                "EQUIPMENT_ID": "MST_EQUIPMENT.EQUIPMENT_ID",
                "PRODUCT_ID":   "MST_PRODUCT.PRODUCT_ID",
            },
            "columns": {
                "DEFECT_ID":       {"type": "VARCHAR(15)",  "nullable": False},
                "LINE_ID":         {"type": "VARCHAR(10)",  "nullable": False},
                "EQUIPMENT_ID":    {"type": "VARCHAR(10)",  "nullable": False},
                "PRODUCT_ID":      {"type": "VARCHAR(10)",  "nullable": False},
                "DEFECT_DATE":     {"type": "DATE",         "nullable": False},
                "DEFECT_TYPE":     {"type": "VARCHAR(15)",  "nullable": False, "description": "치수불량/외관불량/기능불량/용접불량/도장불량/조립불량"},
                "INSPECTED_QTY":   {"type": "INT",          "nullable": False},
                "DEFECT_QTY":      {"type": "INT",          "nullable": False},
                "DEFECT_RATE_PCT": {"type": "DECIMAL(5,2)", "nullable": False},
                "SEVERITY":        {"type": "VARCHAR(10)",  "nullable": False, "description": "CRITICAL/MAJOR/MINOR"},
                "DISPOSITION":     {"type": "VARCHAR(10)",  "nullable": False, "description": "재작업/폐기/특채"},
                "REWORK_COST_KRW": {"type": "INT",          "nullable": True,  "description": "재작업 비용 (재작업이 아닌 경우 NULL)"},
                "ROOT_CAUSE":      {"type": "VARCHAR(20)",  "nullable": True,  "description": "설비마모/원자재불량/작업자오류/공정파라미터/환경요인 (~20% NULL)"},
            },
        },
        "FACT_MAINTENANCE": {
            "description": "정비 기록 (2022-2024)",
            "primary_key": "MAINTENANCE_ID",
            "foreign_keys": {"EQUIPMENT_ID": "MST_EQUIPMENT.EQUIPMENT_ID"},
            "columns": {
                "MAINTENANCE_ID":      {"type": "VARCHAR(15)",  "nullable": False},
                "EQUIPMENT_ID":        {"type": "VARCHAR(10)",  "nullable": False},
                "MAINTENANCE_DATE":    {"type": "DATE",         "nullable": False},
                "MAINTENANCE_TYPE":    {"type": "VARCHAR(10)",  "nullable": False, "description": "예방정비/사후정비/개량정비/긴급정비"},
                "STATUS":              {"type": "VARCHAR(15)",  "nullable": False, "description": "COMPLETED/IN_PROGRESS/SCHEDULED"},
                "PLANNED_HOURS":       {"type": "DECIMAL(4,1)", "nullable": False},
                "ACTUAL_HOURS":        {"type": "DECIMAL(4,1)", "nullable": True,  "description": "SCHEDULED 상태는 NULL"},
                "TECHNICIAN_ID":       {"type": "VARCHAR(10)",  "nullable": False},
                "PARTS_COST_KRW":      {"type": "INT",          "nullable": True,  "description": "~15% NULL"},
                "LABOR_COST_KRW":      {"type": "INT",          "nullable": True},
                "TOTAL_COST_KRW":      {"type": "INT",          "nullable": True,  "description": "SCHEDULED 상태는 NULL"},
                "NEXT_MAINTENANCE_DATE":{"type": "DATE",        "nullable": False},
                "DOWNTIME_HOURS":      {"type": "DECIMAL(4,1)", "nullable": False},
                "RESULT_NOTE":         {"type": "VARCHAR(50)",  "nullable": True,  "description": "~20% NULL"},
            },
        },
    },
}


# ═══════════════════════════════════════════════════════════════
# 8. LOGIC_DOCUMENT.txt
# ═══════════════════════════════════════════════════════════════

LOGIC_DOC = """\
================================================================
스마트팩토리 생산 관리 전략 문서
작성 기준: 2025년 생산 운영 정책
================================================================

1. OEE (종합설비효율) 관리 체계
   OEE = 가용성 × 성능 × 품질
   - 가용성(Availability): 가동시간 / (가동시간 + 비가동시간)
   - 성능(Performance): 실제생산량 / (이론생산량)
   - 품질(Quality): 양품수 / 검사수

   목표: OEE 75% 이상 (세계 수준 85%)
   - 가용성 > 90%, 성능 > 92%, 품질 > 98%

2. 불량률 관리 기준
   등급별 대응:
   - CRITICAL (안전 관련): 즉시 라인 정지, 전수 재검사, 불출 금지
   - MAJOR (기능 영향): 해당 로트 격리, 특별 처리팀 소집
   - MINOR (외관 등): 다음 정기 검사 시 대응

   불량 원인 분석 (5M1E): 사람/기계/재료/방법/측정/환경
   공정 능력 지수: Cpk ≥ 1.33 유지 (Sigma 수준 4이상)

3. 예방정비 (PM) 프로그램
   - A등급 설비 (CNC, 로봇): 30일 주기 정기점검
   - B등급 설비 (프레스, 도장): 60일 주기
   - C등급 설비 (컨베이어 등): 90일 주기

   PM 준수율: 95% 이상 목표
   MTBF (평균고장간격): A등급 720시간 이상
   MTTR (평균수리시간): A등급 4시간 이내

4. 생산 계획 및 부하 관리
   - MRP 기반 생산계획: 주간 계획, 일별 확정
   - 라인 부하율: 80-90% 목표 (과부하/과소 모두 지양)
   - 생산 리드타임: 수주~출하 기준 관리
   - 가동/비가동 시간 기록 의무화 (분 단위)

5. 품질비용 (COPQ) 관리
   - 내부 실패비용: 불량 재작업, 폐기 비용
   - 외부 실패비용: 고객 반품, 보증 수리
   - 예방비용: PM, 교육 훈련
   - 평가비용: 검사, 시험
   목표: COPQ < 총 매출의 2%

6. DEMAND_TYPE별 생산 전략
   - MASS_PRODUCTION: JIT 방식, 작은 로트 빈번 생산
   - SMALL_BATCH: 로트 단위 생산, 셋업 최소화
   - CUSTOM: 주문 확인 후 생산, 특별 공정 관리
   - DISCONTINUE: 잔여 주문만 처리, 설비 전용 계획 수립

7. KPI 정의
   - OEE: 목표 75% / 세계 수준 85%
   - 불량률(PPM): A급 부품 500PPM 이하
   - PM 준수율: 95% 이상
   - 긴급 정비 건수: 월 5건 이하
   - 라인 정지 시간: 계획 대비 5% 이내
"""


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Generating manufacturing demo data...")

    # Master tables
    write_csv("MST_LINE.csv",      LINE_FIELDS,      LINE_ROWS)
    write_csv("MST_EQUIPMENT.csv", EQUIPMENT_FIELDS, EQUIPMENT_ROWS)
    write_csv("MST_PRODUCT.csv",   PRODUCT_FIELDS,   PRODUCT_ROWS)

    # Fact tables
    print("  Generating FACT_PRODUCTION (6 lines × 730 days)...")
    production_rows = generate_production()
    write_csv("FACT_PRODUCTION.csv", PRODUCTION_FIELDS, production_rows)

    print("  Generating FACT_DEFECT (~2000 records)...")
    defect_rows = generate_defects()
    write_csv("FACT_DEFECT.csv", DEFECT_FIELDS, defect_rows)

    print("  Generating FACT_MAINTENANCE (~800 records)...")
    maintenance_rows = generate_maintenance()
    write_csv("FACT_MAINTENANCE.csv", MAINTENANCE_FIELDS, maintenance_rows)

    # Schema JSON
    schema_path = os.path.join(DATA_DIR, "SCHEMA_DEFINITION.json")
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(SCHEMA, f, ensure_ascii=False, indent=2)
    print(f"  Wrote SCHEMA_DEFINITION.json")

    # Logic document
    logic_path = os.path.join(DATA_DIR, "LOGIC_DOCUMENT.txt")
    with open(logic_path, "w", encoding="utf-8") as f:
        f.write(LOGIC_DOC)
    print(f"  Wrote LOGIC_DOCUMENT.txt")

    print("\nDone! All files written to:", DATA_DIR)
