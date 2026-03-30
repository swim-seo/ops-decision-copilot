"""
금융 리스크 및 포트폴리오 관리 데모 데이터 생성기
Korean bank financial risk / portfolio management dataset

Tables:
  - MST_PRODUCT        : 금융 상품 마스터 (25개)
  - MST_CUSTOMER       : 고객 마스터 (50개)
  - MST_BRANCH         : 영업점 마스터 (15개)
  - FACT_TRANSACTION   : 거래 이력 (~20,000건, 2023-2024)
  - FACT_RISK          : 월별 리스크 평가 (고객 × 36개월, 2022-2024)
  - FACT_PERFORMANCE   : 월별 지점 성과 (지점 × 36개월, 2022-2024)
  - SCHEMA_DEFINITION.json
  - LOGIC_DOCUMENT.txt
"""

import csv
import json
import os
import random
from datetime import date, datetime, timedelta

random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "finance")
os.makedirs(DATA_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════════

def write_csv(filename, fieldnames, rows):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows):>7,} rows  →  {filename}")


def maybe_null(value, null_prob=0.20):
    """Return None with probability null_prob, else value."""
    return None if random.random() < null_prob else value


def rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def fmt(d):
    if d is None:
        return ""
    if isinstance(d, (date, datetime)):
        return d.isoformat()
    return d


# ═══════════════════════════════════════════════════════════════
# 1. MST_PRODUCT  — 금융 상품 마스터 (25개)
# ═══════════════════════════════════════════════════════════════

PRODUCT_FIELDS = [
    "PRODUCT_ID", "PRODUCT_NAME", "PRODUCT_TYPE", "CATEGORY",
    "INTEREST_RATE_PCT", "MIN_AMOUNT_KRW", "MAX_AMOUNT_KRW",
    "TERM_MONTHS", "RISK_GRADE", "STATUS", "LAUNCH_DATE", "REGULATOR",
]

PRODUCTS_RAW = [
    # id, name, type, category, rate, min_krw, max_krw, term, risk, status, launch, regulator
    ("PRD001","정기예금(1년)","예금","개인",3.5,1_000_000,500_000_000,12,1,"ACTIVE","2010-03-01","금감원"),
    ("PRD002","정기예금(2년)","예금","개인",4.0,1_000_000,500_000_000,24,1,"ACTIVE","2010-03-01","금감원"),
    ("PRD003","자유적금","적금","개인",4.2,100_000,10_000_000,36,1,"ACTIVE","2012-05-01","금감원"),
    ("PRD004","주택담보대출","대출","개인",5.5,30_000_000,None,120,2,"ACTIVE","2008-01-01","금감원"),
    ("PRD005","신용대출","대출","개인",10.5,1_000_000,100_000_000,60,3,"ACTIVE","2009-06-01","금감원"),
    ("PRD006","기업운전자금대출","대출","기업",6.75,50_000_000,None,12,3,"ACTIVE","2007-01-01","금감원"),
    ("PRD007","국내주식형펀드","펀드","자산관리",None,1_000_000,None,None,4,"ACTIVE","2015-04-01","금융위"),
    ("PRD008","채권형펀드","펀드","자산관리",None,1_000_000,None,None,2,"ACTIVE","2014-09-01","금융위"),
    ("PRD009","달러MMF","펀드","자산관리",None,500_000,None,None,1,"ACTIVE","2016-02-01","금융위"),
    ("PRD010","변액보험(투자형)","보험","자산관리",None,50_000,None,120,4,"ACTIVE","2013-07-01","금융위"),
    ("PRD011","실손보험","보험","개인",None,30_000,None,12,1,"ACTIVE","2011-01-01","금융위"),
    ("PRD012","비자카드(일반)","카드","개인",None,None,None,None,2,"ACTIVE","2010-11-01","금융위"),
    ("PRD013","프리미엄카드(연회비10만)","카드","개인",None,None,None,None,2,"ACTIVE","2017-05-01","금융위"),
    ("PRD014","기업카드","카드","기업",None,None,None,None,2,"ACTIVE","2009-03-01","금융위"),
    ("PRD015","ELS(원금부분보장형)","파생상품","리스크헤지",None,10_000_000,None,36,4,"ACTIVE","2018-01-01","금융위"),
    ("PRD016","ELF(원금비보장형)","파생상품","리스크헤지",None,10_000_000,None,36,5,"ACTIVE","2018-06-01","금융위"),
    ("PRD017","DLS(원자재연계)","파생상품","리스크헤지",None,10_000_000,None,24,5,"ACTIVE","2019-03-01","금융위"),
    ("PRD018","주가지수선물","파생상품","리스크헤지",None,5_000_000,None,3,5,"ACTIVE","2020-01-01","한은"),
    ("PRD019","금리옵션","파생상품","리스크헤지",None,5_000_000,None,6,5,"ACTIVE","2020-06-01","한은"),
    ("PRD020","이자율스왑(IRS)","파생상품","기업",None,100_000_000,None,60,4,"ACTIVE","2016-09-01","한은"),
    ("PRD021","기업정기예금","예금","기업",3.8,10_000_000,None,12,1,"ACTIVE","2008-01-01","금감원"),
    ("PRD022","청년우대적금","적금","개인",5.0,100_000,3_000_000,24,1,"ACTIVE","2022-01-01","금감원"),
    ("PRD023","소호사업자대출","대출","기업",8.0,5_000_000,200_000_000,36,3,"ACTIVE","2019-07-01","금감원"),
    ("PRD024","외화정기예금(USD)","예금","개인",2.5,1_000_000,None,12,2,"ACTIVE","2013-04-01","금감원"),
    ("PRD025","주가연계펀드(구조화)","펀드","자산관리",None,5_000_000,None,36,4,"DISCONTINUED","2021-12-01","금융위"),
]

PRODUCT_IDS = [r[0] for r in PRODUCTS_RAW]

def build_products():
    rows = []
    for (pid, name, ptype, cat, rate, min_a, max_a, term, risk, status, launch, reg) in PRODUCTS_RAW:
        rows.append({
            "PRODUCT_ID": pid,
            "PRODUCT_NAME": name,
            "PRODUCT_TYPE": ptype,
            "CATEGORY": cat,
            "INTEREST_RATE_PCT": rate,
            "MIN_AMOUNT_KRW": min_a,
            "MAX_AMOUNT_KRW": max_a,
            "TERM_MONTHS": term,
            "RISK_GRADE": risk,
            "STATUS": status,
            "LAUNCH_DATE": launch,
            "REGULATOR": reg,
        })
    return rows


# ═══════════════════════════════════════════════════════════════
# 2. MST_CUSTOMER  — 고객 마스터 (50개)
# ═══════════════════════════════════════════════════════════════

CUSTOMER_FIELDS = [
    "CUSTOMER_ID", "CUSTOMER_TYPE", "CUSTOMER_GRADE",
    "AGE_GROUP", "REGION", "CREDIT_SCORE", "TOTAL_ASSETS_MILLION_KRW",
    "RELATIONSHIP_MONTHS", "RISK_APPETITE", "STATUS",
]

CUSTOMER_TYPES = ["개인", "개인", "개인", "법인", "소호"]
CUSTOMER_GRADES = ["VVIP", "VIP", "GOLD", "SILVER", "GENERAL"]
GRADE_WEIGHTS   = [0.04, 0.08, 0.18, 0.30, 0.40]
AGE_GROUPS = ["20대", "30대", "40대", "50대", "60대이상"]
REGIONS = ["서울", "경기", "부산", "대구", "기타"]
REGION_WEIGHTS = [0.40, 0.25, 0.15, 0.10, 0.10]
RISK_APPETITES = ["보수", "중립", "적극"]
STATUSES_CUST = ["ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "DORMANT", "CLOSED"]

def build_customers():
    rows = []
    for i in range(1, 51):
        cid = f"CUS{i:03d}"
        ctype = random.choices(CUSTOMER_TYPES, weights=[3, 3, 3, 1, 2])[0]
        grade = random.choices(CUSTOMER_GRADES, weights=GRADE_WEIGHTS)[0]
        age_group = None if ctype == "법인" else random.choice(AGE_GROUPS)
        region = random.choices(REGIONS, weights=REGION_WEIGHTS)[0]
        credit_score = maybe_null(random.randint(300, 950), null_prob=0.15)
        total_assets = maybe_null(random.randint(50, 50_000), null_prob=0.20)
        rel_months = random.randint(1, 240)
        risk_app = random.choice(RISK_APPETITES)
        status = random.choices(STATUSES_CUST, weights=[4, 4, 4, 4, 1, 1])[0]
        rows.append({
            "CUSTOMER_ID": cid,
            "CUSTOMER_TYPE": ctype,
            "CUSTOMER_GRADE": grade,
            "AGE_GROUP": age_group,
            "REGION": region,
            "CREDIT_SCORE": credit_score,
            "TOTAL_ASSETS_MILLION_KRW": total_assets,
            "RELATIONSHIP_MONTHS": rel_months,
            "RISK_APPETITE": risk_app,
            "STATUS": status,
        })
    return rows


# ═══════════════════════════════════════════════════════════════
# 3. MST_BRANCH  — 영업점 마스터 (15개)
# ═══════════════════════════════════════════════════════════════

BRANCH_FIELDS = [
    "BRANCH_ID", "BRANCH_NAME", "BRANCH_TYPE", "REGION",
    "ADDRESS", "MANAGER_NAME", "OPEN_DATE", "EMPLOYEE_COUNT", "STATUS",
]

BRANCHES_RAW = [
    ("BRN001","본점영업부","본점","서울","서울 중구 을지로 100","김태호","2000-01-03",120,"OPERATING"),
    ("BRN002","강남지점","지점","서울","서울 강남구 테헤란로 200","이수진","2003-05-12",45,"OPERATING"),
    ("BRN003","여의도지점","지점","서울","서울 영등포구 여의대로 50","박민준","2005-03-07",38,"OPERATING"),
    ("BRN004","마포지점","지점","서울","서울 마포구 공덕동 300","최지연","2008-09-01",28,"OPERATING"),
    ("BRN005","수원지점","지점","경기","경기 수원시 팔달구 매산로 15","정하늘","2010-04-05",32,"OPERATING"),
    ("BRN006","성남지점","지점","경기","경기 성남시 분당구 판교로 88","한승우","2012-07-02",25,"OPERATING"),
    ("BRN007","인천지점","지점","경기","인천 연수구 컨벤시아대로 204","오유리","2009-11-10",30,"OPERATING"),
    ("BRN008","부산지점","지점","부산","부산 해운대구 센텀중앙로 79","임태양","2006-02-14",35,"OPERATING"),
    ("BRN009","부산서면출장소","출장소","부산","부산 부산진구 서면로 12","송다영","2015-06-01",8,"OPERATING"),
    ("BRN010","대구지점","지점","대구","대구 수성구 범어대로 100","권민서","2011-10-03",22,"OPERATING"),
    ("BRN011","대구출장소","출장소","대구","대구 중구 동성로 45","유재원","2018-03-05",6,"OPERATING"),
    ("BRN012","디지털지점","디지털지점","서울","서울 강서구 마곡중앙로 161",None,"2021-01-11",15,"OPERATING"),
    ("BRN013","광주지점","지점","기타","광주 서구 상무대로 911","배소연","2014-08-04",20,"OPERATING"),
    ("BRN014","대전지점","지점","기타","대전 유성구 엑스포로 107","윤세준","2013-12-02",18,"OPERATING"),
    ("BRN015","제주출장소","출장소","기타","제주 제주시 중앙로 55","신나은","2019-05-20",5,"RENOVATION"),
]

BRANCH_IDS = [r[0] for r in BRANCHES_RAW]

# Branch size multiplier (for performance generation)
BRANCH_SIZE = {
    "BRN001": 5.0, "BRN002": 3.5, "BRN003": 3.0, "BRN004": 2.0,
    "BRN005": 2.5, "BRN006": 2.0, "BRN007": 2.2, "BRN008": 2.8,
    "BRN009": 0.4, "BRN010": 1.8, "BRN011": 0.3, "BRN012": 1.0,
    "BRN013": 1.5, "BRN014": 1.4, "BRN015": 0.2,
}

def build_branches():
    rows = []
    for (bid, name, btype, region, addr, mgr, open_d, emp, status) in BRANCHES_RAW:
        rows.append({
            "BRANCH_ID": bid,
            "BRANCH_NAME": name,
            "BRANCH_TYPE": btype,
            "REGION": region,
            "ADDRESS": addr,
            "MANAGER_NAME": mgr,
            "OPEN_DATE": open_d,
            "EMPLOYEE_COUNT": emp,
            "STATUS": status,
        })
    return rows


# ═══════════════════════════════════════════════════════════════
# 4. FACT_TRANSACTION  — 거래 이력 (~20,000건, 2023-2024)
# ═══════════════════════════════════════════════════════════════

TRANSACTION_FIELDS = [
    "TRANSACTION_ID", "CUSTOMER_ID", "PRODUCT_ID", "BRANCH_ID",
    "TRANSACTION_DATE", "TRANSACTION_TIME", "TRANSACTION_TYPE",
    "AMOUNT_KRW", "BALANCE_AFTER_KRW", "CHANNEL",
    "CURRENCY", "IS_ANOMALY", "ANOMALY_TYPE", "STATUS",
]

TX_TYPES = ["입금", "출금", "이체", "매수", "매도", "대출실행", "대출상환", "카드결제", "외환거래"]
TX_TYPE_WEIGHTS = [0.20, 0.18, 0.22, 0.08, 0.07, 0.05, 0.05, 0.10, 0.05]
CHANNELS = ["영업점", "ATM", "인터넷뱅킹", "모바일앱", "자동이체"]
CHANNEL_WEIGHTS = [0.12, 0.18, 0.25, 0.38, 0.07]
CURRENCIES = ["KRW", "KRW", "KRW", "KRW", "KRW", "USD", "EUR", "JPY"]
TX_STATUSES = ["COMPLETED", "COMPLETED", "COMPLETED", "COMPLETED", "FAILED", "REVERSED", "PENDING"]

# product-type → suitable transaction types
PRODUCT_TX_MAP = {
    "예금": ["입금", "출금", "이체", "자동이체"],
    "적금": ["입금", "자동이체"],
    "대출": ["대출실행", "대출상환"],
    "펀드": ["매수", "매도"],
    "보험": ["입금", "자동이체"],
    "카드": ["카드결제"],
    "파생상품": ["매수", "매도", "외환거래"],
}

# product_id → type lookup
PTYPE_LOOKUP = {r[0]: r[2] for r in PRODUCTS_RAW}

ANOMALY_TYPES = ["이상금액", "비정상시간", "연속거래", "해외거래이상", "계좌분산"]

def monthly_volume_factor(month: int) -> float:
    """Seasonal weight per calendar month."""
    factors = {1: 1.15, 2: 0.85, 3: 1.00, 4: 1.00, 5: 1.00,
               6: 1.00, 7: 1.00, 8: 1.00, 9: 1.05, 10: 1.05,
               11: 1.10, 12: 1.25}
    return factors.get(month, 1.0)

def rand_amount(ctype: str) -> int:
    if ctype == "법인":
        return random.randint(1_000_000, 5_000_000_000)
    elif ctype == "소호":
        return random.randint(500_000, 500_000_000)
    else:
        return random.randint(10_000, 200_000_000)

def build_transactions(customers, products):
    cust_map = {c["CUSTOMER_ID"]: c for c in customers}
    prod_map = {p["PRODUCT_ID"]: p for p in products}

    active_prod_ids = [p["PRODUCT_ID"] for p in products if p["STATUS"] == "ACTIVE"]

    rows = []
    tx_counter = 1
    TARGET = 20_000

    start_date = date(2023, 1, 1)
    end_date   = date(2024, 12, 31)
    total_days = (end_date - start_date).days + 1

    # Build day list with seasonal weights
    all_days = [start_date + timedelta(days=d) for d in range(total_days)]
    day_weights = [monthly_volume_factor(d.month) for d in all_days]
    total_w = sum(day_weights)
    day_weights = [w / total_w for w in day_weights]

    # Pre-generate customer-product assignments for realism
    # Each customer has 1-5 active products
    cust_products = {}
    for c in customers:
        cid = c["CUSTOMER_ID"]
        n = random.randint(1, 5)
        cust_products[cid] = random.sample(active_prod_ids, min(n, len(active_prod_ids)))

    # Track recent transactions per customer for 연속거래 anomaly simulation
    # (date -> list of times)
    cust_tx_times: dict = {}  # cid -> list of (date, hour, minute)

    # Anomaly pool: 3% = 600 anomaly records, assign randomly
    anomaly_indices = set(random.sample(range(TARGET), int(TARGET * 0.03)))

    # Stratify anomaly types
    anomaly_type_pool = []
    weights_anomaly = [0.30, 0.20, 0.20, 0.15, 0.15]
    for atype, w in zip(ANOMALY_TYPES, weights_anomaly):
        anomaly_type_pool.extend([atype] * int(w * 100))

    sampled_days = random.choices(all_days, weights=day_weights, k=TARGET)
    sampled_days.sort()

    for idx in range(TARGET):
        tx_id = f"TXN{tx_counter:08d}"
        tx_counter += 1

        cid = random.choice([c["CUSTOMER_ID"] for c in customers])
        cust = cust_map[cid]

        prods_for_cust = cust_products.get(cid, active_prod_ids[:3])
        pid = random.choice(prods_for_cust)
        prod = prod_map[pid]
        ptype = PTYPE_LOOKUP.get(pid, "예금")

        tx_date = sampled_days[idx]

        is_anomaly_record = idx in anomaly_indices
        anomaly_type = None
        tx_hour = None
        tx_minute = random.randint(0, 59)

        if is_anomaly_record:
            atype = random.choice(anomaly_type_pool)
            anomaly_type = atype
            if atype == "비정상시간":
                tx_hour = random.randint(2, 3)
            else:
                # Stock hours or random
                if ptype == "펀드":
                    tx_hour = random.randint(9, 15)
                else:
                    tx_hour = random.randint(8, 22)
        else:
            if ptype == "펀드":
                # Higher probability during market hours
                if random.random() < 0.70:
                    tx_hour = random.randint(9, 15)
                else:
                    tx_hour = random.randint(8, 22)
            else:
                tx_hour = random.randint(8, 22)

        tx_time = f"{tx_hour:02d}:{tx_minute:02d}:{random.randint(0,59):02d}"

        # Determine suitable tx types
        suitable_types = PRODUCT_TX_MAP.get(ptype, TX_TYPES)
        tx_type = random.choice(suitable_types)

        # Amount
        base_amount = rand_amount(cust["CUSTOMER_TYPE"])
        if is_anomaly_record and anomaly_type == "이상금액":
            base_amount = base_amount * random.randint(5, 20)
        if is_anomaly_record and anomaly_type == "계좌분산":
            # Just under 10M threshold
            base_amount = random.randint(9_000_000, 9_900_000)
        amount = max(10_000, base_amount)

        balance_after = maybe_null(amount + random.randint(100_000, 50_000_000), null_prob=0.10)

        # Channel: online 40% → no branch
        channel = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0]
        if channel in ("인터넷뱅킹", "모바일앱", "자동이체"):
            branch_id = None
        else:
            branch_id = random.choice(BRANCH_IDS)

        # Currency: foreign if 외환거래 or anomaly 해외거래이상
        if tx_type == "외환거래" or (is_anomaly_record and anomaly_type == "해외거래이상"):
            currency = random.choice(["USD", "EUR", "JPY"])
        else:
            currency = "KRW"

        status = random.choices(TX_STATUSES, weights=[4, 4, 4, 4, 0.3, 0.2, 0.1])[0]

        rows.append({
            "TRANSACTION_ID": tx_id,
            "CUSTOMER_ID": cid,
            "PRODUCT_ID": pid,
            "BRANCH_ID": branch_id,
            "TRANSACTION_DATE": tx_date.isoformat(),
            "TRANSACTION_TIME": tx_time,
            "TRANSACTION_TYPE": tx_type,
            "AMOUNT_KRW": amount,
            "BALANCE_AFTER_KRW": balance_after,
            "CHANNEL": channel,
            "CURRENCY": currency,
            "IS_ANOMALY": "Y" if is_anomaly_record else "N",
            "ANOMALY_TYPE": anomaly_type,
            "STATUS": status,
        })

    return rows


# ═══════════════════════════════════════════════════════════════
# 5. FACT_RISK  — 월별 리스크 평가 (고객 × 36개월, 2022-2024)
# ═══════════════════════════════════════════════════════════════

RISK_FIELDS = [
    "RISK_ID", "CUSTOMER_ID", "YEAR_MONTH",
    "CREDIT_SCORE_CURRENT", "PD_PCT", "LGD_PCT", "EAD_KRW",
    "EXPECTED_LOSS_KRW", "RISK_GRADE", "RISK_GRADE_PREV", "GRADE_CHANGE",
    "COLLATERAL_VALUE_KRW", "MARKET_RISK_VAR_KRW", "LIQUIDITY_RISK_SCORE",
]

RISK_GRADES = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D"]
GRADE_IDX = {g: i for i, g in enumerate(RISK_GRADES)}

# Economic stress periods: more downgrades
STRESS_PERIODS = {
    # year-month -> stress level 0..1
    "2022-10": 0.6, "2022-11": 0.7, "2022-12": 0.6,
    "2023-04": 0.5, "2023-05": 0.7, "2023-06": 0.6,
}

def initial_grade_for_customer(cust) -> str:
    score = cust.get("CREDIT_SCORE")
    if score is None:
        return random.choice(["BBB", "BB", "A"])
    if score >= 900: return "AAA"
    if score >= 850: return "AA"
    if score >= 800: return "A"
    if score >= 700: return "BBB"
    if score >= 600: return "BB"
    if score >= 500: return "B"
    if score >= 400: return "CCC"
    return "D"

def pd_for_grade(grade: str) -> float:
    base = {"AAA": 0.01, "AA": 0.05, "A": 0.15, "BBB": 0.50,
            "BB": 1.50, "B": 4.00, "CCC": 9.00, "D": 15.0}
    return base.get(grade, 1.0) + random.uniform(-0.01, 0.01) * base.get(grade, 1.0)

def lgd_for_collateral(has_collateral: bool) -> float:
    if has_collateral:
        return round(random.uniform(20, 45), 2)
    else:
        return round(random.uniform(55, 80), 2)

def build_risk(customers):
    rows = []
    risk_counter = 1

    # Generate year-month list: 2022-01 .. 2024-12 (36 months)
    year_months = []
    for yr in range(2022, 2025):
        for mo in range(1, 13):
            year_months.append(f"{yr}-{mo:02d}")

    # Customers that will experience grade changes (~10%)
    n_change_customers = max(1, int(len(customers) * 0.10))
    change_customers = set(random.sample([c["CUSTOMER_ID"] for c in customers], n_change_customers))

    for cust in customers:
        cid = cust["CUSTOMER_ID"]
        current_grade = initial_grade_for_customer(cust)
        prev_grade = None

        # Decide change months for this customer
        change_months_set = set()
        if cid in change_customers:
            num_changes = random.randint(1, 2)
            change_months_set = set(random.sample(range(1, 36), num_changes))

        # Base credit score drift
        base_score = cust.get("CREDIT_SCORE") or random.randint(500, 850)

        # Investment products for market VaR
        has_investment = random.random() < 0.50

        for month_idx, ym in enumerate(year_months):
            rid = f"RSK{risk_counter:08d}"
            risk_counter += 1

            # Credit score fluctuates ±30 monthly
            cs = max(300, min(950, base_score + random.randint(-30, 30)))

            # Stress period influence
            stress = STRESS_PERIODS.get(ym, 0.0)

            # Grade change logic
            grade_change = None
            if prev_grade is None:
                grade_change = None
            elif month_idx in change_months_set:
                # Stress → more likely downgrade
                if stress > 0.5 or random.random() < 0.40 + stress:
                    # Downgrade
                    idx = GRADE_IDX[current_grade]
                    if idx < len(RISK_GRADES) - 1:
                        current_grade = RISK_GRADES[idx + 1]
                    grade_change = "DOWNGRADE"
                else:
                    # Upgrade
                    idx = GRADE_IDX[current_grade]
                    if idx > 0:
                        current_grade = RISK_GRADES[idx - 1]
                    grade_change = "UPGRADE"
            else:
                # Stress may cause spontaneous downgrade
                if stress > 0.5 and random.random() < stress * 0.15:
                    idx = GRADE_IDX[current_grade]
                    if idx < len(RISK_GRADES) - 1:
                        current_grade = RISK_GRADES[idx + 1]
                    grade_change = "DOWNGRADE"
                else:
                    grade_change = "STABLE"

            pd_val = round(pd_for_grade(current_grade), 4)
            has_collateral = random.random() > 0.35
            lgd_val = lgd_for_collateral(has_collateral)

            # EAD: depends on customer type
            if cust["CUSTOMER_TYPE"] == "법인":
                ead = random.randint(100_000_000, 50_000_000_000)
            elif cust["CUSTOMER_TYPE"] == "소호":
                ead = random.randint(10_000_000, 2_000_000_000)
            else:
                ead = random.randint(1_000_000, 500_000_000)

            el = round(pd_val / 100 * lgd_val / 100 * ead)

            collateral_val = maybe_null(
                int(ead * random.uniform(0.8, 1.5)),
                null_prob=0.35 if not has_collateral else 0.0,
            )

            market_var = maybe_null(
                random.randint(500_000, 100_000_000),
                null_prob=0.0 if has_investment else 1.0,
            )

            liquidity_score = random.randint(1, 10)

            rows.append({
                "RISK_ID": rid,
                "CUSTOMER_ID": cid,
                "YEAR_MONTH": ym,
                "CREDIT_SCORE_CURRENT": cs,
                "PD_PCT": pd_val,
                "LGD_PCT": lgd_val,
                "EAD_KRW": ead,
                "EXPECTED_LOSS_KRW": el,
                "RISK_GRADE": current_grade,
                "RISK_GRADE_PREV": prev_grade,
                "GRADE_CHANGE": grade_change,
                "COLLATERAL_VALUE_KRW": collateral_val,
                "MARKET_RISK_VAR_KRW": market_var,
                "LIQUIDITY_RISK_SCORE": liquidity_score,
            })

            prev_grade = current_grade

    return rows


# ═══════════════════════════════════════════════════════════════
# 6. FACT_PERFORMANCE  — 월별 지점 성과 (15 × 36개월)
# ═══════════════════════════════════════════════════════════════

PERFORMANCE_FIELDS = [
    "PERF_ID", "BRANCH_ID", "YEAR_MONTH",
    "NEW_CUSTOMER_COUNT", "CLOSED_CUSTOMER_COUNT",
    "TOTAL_DEPOSIT_KRW", "TOTAL_LOAN_KRW", "TOTAL_INVESTMENT_KRW",
    "NET_INTEREST_INCOME_KRW", "FEE_INCOME_KRW", "TOTAL_REVENUE_KRW",
    "OPERATING_COST_KRW", "NET_PROFIT_KRW",
    "NPS_SCORE", "COMPLAINT_COUNT", "LOAN_DEFAULT_COUNT",
]

def quarterly_factor(month: int) -> float:
    """Q4 strong, Q1 slightly weak."""
    q = (month - 1) // 3 + 1
    return {1: 0.92, 2: 0.98, 3: 1.02, 4: 1.10}.get(q, 1.0)

def build_performance():
    rows = []
    perf_counter = 1

    year_months = []
    for yr in range(2022, 2025):
        for mo in range(1, 13):
            year_months.append((yr, mo, f"{yr}-{mo:02d}"))

    for bid, bname, btype, *_ in BRANCHES_RAW:
        size = BRANCH_SIZE.get(bid, 1.0)
        # Base monthly deposit (KRW) — scales with size
        base_deposit = size * 50_000_000_000  # 500억 기준 × size
        base_loan    = size * 35_000_000_000
        base_invest  = size * 15_000_000_000

        for yr, mo, ym in year_months:
            qf = quarterly_factor(mo)
            sf = monthly_volume_factor(mo)
            combined = (qf + sf) / 2

            noise = lambda: random.uniform(0.90, 1.10)

            deposit   = int(base_deposit * combined * noise())
            loan      = int(base_loan    * combined * noise())
            invest    = int(base_invest  * combined * noise())

            # NIM 1.5-2.5% of loan balance (monthly → /12)
            nim_rate  = random.uniform(0.015, 0.025) / 12
            nii       = int(loan * nim_rate)

            fee_income = int(size * random.uniform(50_000_000, 200_000_000) * combined)
            total_rev  = nii + fee_income

            op_cost    = int(total_rev * random.uniform(0.55, 0.75))
            net_profit = total_rev - op_cost

            nps        = maybe_null(random.randint(-20, 80), null_prob=0.15)
            complaints = random.randint(0, int(size * 10))
            defaults   = maybe_null(random.randint(0, int(size * 3)), null_prob=0.20)

            new_cust   = random.randint(int(size * 2), int(size * 20 + 5))
            closed_cust = random.randint(0, max(1, int(size * 3)))

            rows.append({
                "PERF_ID": f"PFM{perf_counter:07d}",
                "BRANCH_ID": bid,
                "YEAR_MONTH": ym,
                "NEW_CUSTOMER_COUNT": new_cust,
                "CLOSED_CUSTOMER_COUNT": closed_cust,
                "TOTAL_DEPOSIT_KRW": deposit,
                "TOTAL_LOAN_KRW": loan,
                "TOTAL_INVESTMENT_KRW": invest,
                "NET_INTEREST_INCOME_KRW": nii,
                "FEE_INCOME_KRW": fee_income,
                "TOTAL_REVENUE_KRW": total_rev,
                "OPERATING_COST_KRW": op_cost,
                "NET_PROFIT_KRW": net_profit,
                "NPS_SCORE": nps,
                "COMPLAINT_COUNT": complaints,
                "LOAN_DEFAULT_COUNT": defaults,
            })
            perf_counter += 1

    return rows


# ═══════════════════════════════════════════════════════════════
# 7. SCHEMA_DEFINITION.json
# ═══════════════════════════════════════════════════════════════

SCHEMA = {
    "dataset": "finance",
    "description": "Korean bank financial risk and portfolio management demo dataset",
    "generated_at": "2025-01-01",
    "tables": {
        "MST_PRODUCT": {
            "description": "금융 상품 마스터 (25개)",
            "primary_key": "PRODUCT_ID",
            "columns": {
                "PRODUCT_ID": {"type": "VARCHAR(6)", "nullable": False, "description": "상품 고유 코드 (PRD001~PRD025)"},
                "PRODUCT_NAME": {"type": "VARCHAR(50)", "nullable": False, "description": "상품명"},
                "PRODUCT_TYPE": {"type": "VARCHAR(10)", "nullable": False, "description": "상품 유형: 예금/적금/대출/펀드/보험/카드/파생상품"},
                "CATEGORY": {"type": "VARCHAR(10)", "nullable": False, "description": "분류: 개인/기업/자산관리/리스크헤지"},
                "INTEREST_RATE_PCT": {"type": "DECIMAL(5,2)", "nullable": True, "description": "기본 금리(%). 비이자 상품은 NULL"},
                "MIN_AMOUNT_KRW": {"type": "BIGINT", "nullable": True, "description": "최소 가입금액(원)"},
                "MAX_AMOUNT_KRW": {"type": "BIGINT", "nullable": True, "description": "최대 가입금액(원). 한도없음=NULL"},
                "TERM_MONTHS": {"type": "INT", "nullable": True, "description": "계약 기간(월). 수시입출금=NULL"},
                "RISK_GRADE": {"type": "INT", "nullable": False, "description": "리스크 등급 1(최저)~5(최고)"},
                "STATUS": {"type": "VARCHAR(15)", "nullable": False, "description": "상태: ACTIVE/DISCONTINUED/SUSPENDED"},
                "LAUNCH_DATE": {"type": "DATE", "nullable": False, "description": "출시일"},
                "REGULATOR": {"type": "VARCHAR(10)", "nullable": False, "description": "감독기관: 금융위/금감원/한은"},
            },
        },
        "MST_CUSTOMER": {
            "description": "고객 마스터 (50개, 개인/법인/소호 혼합)",
            "primary_key": "CUSTOMER_ID",
            "columns": {
                "CUSTOMER_ID": {"type": "VARCHAR(6)", "nullable": False, "description": "고객 고유 코드 (CUS001~CUS050)"},
                "CUSTOMER_TYPE": {"type": "VARCHAR(5)", "nullable": False, "description": "고객 유형: 개인/법인/소호"},
                "CUSTOMER_GRADE": {"type": "VARCHAR(8)", "nullable": False, "description": "등급: VVIP/VIP/GOLD/SILVER/GENERAL"},
                "AGE_GROUP": {"type": "VARCHAR(8)", "nullable": True, "description": "연령대 (법인=NULL)"},
                "REGION": {"type": "VARCHAR(5)", "nullable": False, "description": "지역: 서울/경기/부산/대구/기타"},
                "CREDIT_SCORE": {"type": "INT", "nullable": True, "description": "신용점수 300~950 (일부 NULL)"},
                "TOTAL_ASSETS_MILLION_KRW": {"type": "BIGINT", "nullable": True, "description": "총자산(백만원, 일부 NULL)"},
                "RELATIONSHIP_MONTHS": {"type": "INT", "nullable": False, "description": "거래기간(월)"},
                "RISK_APPETITE": {"type": "VARCHAR(5)", "nullable": False, "description": "투자 성향: 보수/중립/적극"},
                "STATUS": {"type": "VARCHAR(10)", "nullable": False, "description": "상태: ACTIVE/DORMANT/CLOSED"},
            },
        },
        "MST_BRANCH": {
            "description": "영업점 마스터 (15개)",
            "primary_key": "BRANCH_ID",
            "columns": {
                "BRANCH_ID": {"type": "VARCHAR(6)", "nullable": False, "description": "지점 코드 (BRN001~BRN015)"},
                "BRANCH_NAME": {"type": "VARCHAR(30)", "nullable": False, "description": "지점명"},
                "BRANCH_TYPE": {"type": "VARCHAR(10)", "nullable": False, "description": "유형: 본점/지점/출장소/디지털지점"},
                "REGION": {"type": "VARCHAR(5)", "nullable": False, "description": "지역"},
                "ADDRESS": {"type": "VARCHAR(100)", "nullable": False, "description": "주소"},
                "MANAGER_NAME": {"type": "VARCHAR(10)", "nullable": True, "description": "지점장 이름 (디지털지점 NULL 가능)"},
                "OPEN_DATE": {"type": "DATE", "nullable": False, "description": "개점일"},
                "EMPLOYEE_COUNT": {"type": "INT", "nullable": False, "description": "직원 수"},
                "STATUS": {"type": "VARCHAR(15)", "nullable": False, "description": "운영 상태: OPERATING/RENOVATION/CLOSED"},
            },
        },
        "FACT_TRANSACTION": {
            "description": "거래 이력 (~20,000건, 2023-01-01~2024-12-31)",
            "primary_key": "TRANSACTION_ID",
            "foreign_keys": {"CUSTOMER_ID": "MST_CUSTOMER.CUSTOMER_ID", "PRODUCT_ID": "MST_PRODUCT.PRODUCT_ID", "BRANCH_ID": "MST_BRANCH.BRANCH_ID"},
            "columns": {
                "TRANSACTION_ID": {"type": "VARCHAR(11)", "nullable": False, "description": "거래 고유 ID (TXN00000001~)"},
                "CUSTOMER_ID": {"type": "VARCHAR(6)", "nullable": False, "description": "고객 ID (FK → MST_CUSTOMER)"},
                "PRODUCT_ID": {"type": "VARCHAR(6)", "nullable": False, "description": "상품 ID (FK → MST_PRODUCT)"},
                "BRANCH_ID": {"type": "VARCHAR(6)", "nullable": True, "description": "지점 ID (온라인 거래=NULL, FK → MST_BRANCH)"},
                "TRANSACTION_DATE": {"type": "DATE", "nullable": False, "description": "거래일"},
                "TRANSACTION_TIME": {"type": "TIME", "nullable": False, "description": "거래 시각 (HH:MM:SS)"},
                "TRANSACTION_TYPE": {"type": "VARCHAR(10)", "nullable": False, "description": "거래 유형: 입금/출금/이체/매수/매도/대출실행/대출상환/카드결제/외환거래"},
                "AMOUNT_KRW": {"type": "BIGINT", "nullable": False, "description": "거래 금액(원). 외화 거래도 원화 환산"},
                "BALANCE_AFTER_KRW": {"type": "BIGINT", "nullable": True, "description": "거래 후 잔액(원), 일부 NULL"},
                "CHANNEL": {"type": "VARCHAR(10)", "nullable": False, "description": "채널: 영업점/ATM/인터넷뱅킹/모바일앱/자동이체"},
                "CURRENCY": {"type": "VARCHAR(3)", "nullable": False, "description": "통화: KRW/USD/EUR/JPY"},
                "IS_ANOMALY": {"type": "CHAR(1)", "nullable": False, "description": "이상거래 여부: Y/N"},
                "ANOMALY_TYPE": {"type": "VARCHAR(10)", "nullable": True, "description": "이상 유형 (정상=NULL): 이상금액/비정상시간/연속거래/해외거래이상/계좌분산"},
                "STATUS": {"type": "VARCHAR(10)", "nullable": False, "description": "처리 상태: COMPLETED/FAILED/REVERSED/PENDING"},
            },
        },
        "FACT_RISK": {
            "description": "월별 고객 리스크 평가 (50고객 × 36개월 = 1,800행, 2022-01~2024-12)",
            "primary_key": "RISK_ID",
            "foreign_keys": {"CUSTOMER_ID": "MST_CUSTOMER.CUSTOMER_ID"},
            "columns": {
                "RISK_ID": {"type": "VARCHAR(11)", "nullable": False, "description": "리스크 레코드 ID (RSK00000001~)"},
                "CUSTOMER_ID": {"type": "VARCHAR(6)", "nullable": False, "description": "고객 ID (FK → MST_CUSTOMER)"},
                "YEAR_MONTH": {"type": "VARCHAR(7)", "nullable": False, "description": "기준 연월 (YYYY-MM)"},
                "CREDIT_SCORE_CURRENT": {"type": "INT", "nullable": False, "description": "당월 신용점수 (월별 변동)"},
                "PD_PCT": {"type": "DECIMAL(6,4)", "nullable": False, "description": "부도확률 PD (%)"},
                "LGD_PCT": {"type": "DECIMAL(5,2)", "nullable": False, "description": "부도시 손실률 LGD (%)"},
                "EAD_KRW": {"type": "BIGINT", "nullable": False, "description": "부도시 노출액 EAD (원)"},
                "EXPECTED_LOSS_KRW": {"type": "BIGINT", "nullable": False, "description": "예상손실 EL = PD × LGD × EAD (원)"},
                "RISK_GRADE": {"type": "VARCHAR(3)", "nullable": False, "description": "내부 신용등급: AAA/AA/A/BBB/BB/B/CCC/D"},
                "RISK_GRADE_PREV": {"type": "VARCHAR(3)", "nullable": True, "description": "전월 신용등급 (첫 월=NULL)"},
                "GRADE_CHANGE": {"type": "VARCHAR(10)", "nullable": True, "description": "등급 변동: UPGRADE/DOWNGRADE/STABLE (첫 월=NULL)"},
                "COLLATERAL_VALUE_KRW": {"type": "BIGINT", "nullable": True, "description": "담보 평가액 (무담보=NULL, ~35%)"},
                "MARKET_RISK_VAR_KRW": {"type": "BIGINT", "nullable": True, "description": "시장리스크 VaR 95% 1일기준 (비투자상품=NULL, ~50%)"},
                "LIQUIDITY_RISK_SCORE": {"type": "INT", "nullable": False, "description": "유동성 리스크 점수 1(낮음)~10(높음)"},
            },
        },
        "FACT_PERFORMANCE": {
            "description": "월별 지점 성과 (15지점 × 36개월 = 540행, 2022-01~2024-12)",
            "primary_key": "PERF_ID",
            "foreign_keys": {"BRANCH_ID": "MST_BRANCH.BRANCH_ID"},
            "columns": {
                "PERF_ID": {"type": "VARCHAR(10)", "nullable": False, "description": "성과 레코드 ID (PFM0000001~)"},
                "BRANCH_ID": {"type": "VARCHAR(6)", "nullable": False, "description": "지점 ID (FK → MST_BRANCH)"},
                "YEAR_MONTH": {"type": "VARCHAR(7)", "nullable": False, "description": "기준 연월 (YYYY-MM)"},
                "NEW_CUSTOMER_COUNT": {"type": "INT", "nullable": False, "description": "신규 고객 수"},
                "CLOSED_CUSTOMER_COUNT": {"type": "INT", "nullable": False, "description": "해지 고객 수"},
                "TOTAL_DEPOSIT_KRW": {"type": "BIGINT", "nullable": False, "description": "총 수신 잔액(원)"},
                "TOTAL_LOAN_KRW": {"type": "BIGINT", "nullable": False, "description": "총 여신 잔액(원)"},
                "TOTAL_INVESTMENT_KRW": {"type": "BIGINT", "nullable": False, "description": "총 투자 잔액(원)"},
                "NET_INTEREST_INCOME_KRW": {"type": "BIGINT", "nullable": False, "description": "순이자이익(원)"},
                "FEE_INCOME_KRW": {"type": "BIGINT", "nullable": False, "description": "수수료 수익(원)"},
                "TOTAL_REVENUE_KRW": {"type": "BIGINT", "nullable": False, "description": "총 수익 = NII + 수수료 (원)"},
                "OPERATING_COST_KRW": {"type": "BIGINT", "nullable": False, "description": "운영 비용(원)"},
                "NET_PROFIT_KRW": {"type": "BIGINT", "nullable": False, "description": "순이익 = 수익 - 비용 (원)"},
                "NPS_SCORE": {"type": "INT", "nullable": True, "description": "순추천고객지수 NPS (-100~100, ~15% NULL)"},
                "COMPLAINT_COUNT": {"type": "INT", "nullable": False, "description": "민원 건수"},
                "LOAN_DEFAULT_COUNT": {"type": "INT", "nullable": True, "description": "여신 연체/부실 건수 (~20% NULL)"},
            },
        },
    },
}


# ═══════════════════════════════════════════════════════════════
# 8. LOGIC_DOCUMENT.txt
# ═══════════════════════════════════════════════════════════════

LOGIC_DOC = """\
================================================================
금융 리스크 및 포트폴리오 관리 전략 문서
작성 기준: 2025년 리스크 관리 정책 (바젤III/K-IFRs 기준)
================================================================

1. 신용 리스크 관리 체계
   내부 신용등급 체계 (IRB 접근법):
   - AAA~A: 투자등급, 충당금 최소화
   - BBB~BB: 요주의 등급, 분기 모니터링
   - B~CCC: 부실 위험, 월간 집중 관리
   - D: 부실, 전액 손상차손 처리

   예상손실(EL) = PD × LGD × EAD
   - PD (부도확률): 과거 3년 실적 기반 추정
   - LGD (부도시 손실률): 담보 유형별 차등 (부동산 30%, 무담보 65%)
   - EAD (부도시 노출액): 여신잔액 + 미사용 한도

2. 이상거래 탐지 (FDS - Fraud Detection System)
   Rule-based 이상 징후:
   - 이상금액: 고객 평균 거래액 대비 10배 초과
   - 비정상시간: 02:00-04:00 고액 거래
   - 연속거래: 10분 내 동일 계좌 5회 이상
   - 계좌분산: 1일 내 동일 수취인 다수 소액 이체 (구조화 거래)
   - 해외이상: 평소 거래 없는 국가 외환 거래

   탐지 후 처리 프로세스:
   1단계: 자동 알림 발생
   2단계: 담당자 검토 (15분 이내)
   3단계: 고객 확인 전화
   4단계: 거래 차단/허용 결정

3. 시장 리스크 관리
   VaR (Value at Risk) 기준:
   - 신뢰수준: 95% (1일 기준)
   - 보유기간: 10일 (BIS 기준)
   - 모델: Historical Simulation (250거래일)

   한도 관리:
   - 전체 포트폴리오 VaR: 자기자본의 3% 이내
   - 개별 상품 VaR: 포트폴리오 VaR의 20% 이내

4. 유동성 리스크 관리
   LCR (유동성커버리지비율) >= 100% 유지
   - 고유동성자산(HQLA): 현금 + 국채 + 우량 회사채
   - 30일 순현금유출 대비 HQLA 비율

   NSFR (순안정조달비율) >= 100%
   - 장기 조달 / 장기 운용

5. 금리 리스크
   NIM (순이자마진) 관리:
   - 목표 NIM: 2.0-2.5%
   - 금리 민감도: BPV (basis point value) 한도 설정
   - 재조달 주기: 단기 수신 < 장기 여신 (duration gap 관리)

6. 규제 자본 관리 (바젤III)
   BIS 자기자본비율 >= 13.0% (내부 목표)
   - CET1 (보통주 자본) >= 9.5%
   - Tier1 >= 11.0%
   - 총 자본 >= 13.0%

7. KPI 정의
   - 고정이하 여신 비율(NPL): 1.0% 이하
   - 연체율: 0.8% 이하
   - 충당금 커버리지: 150% 이상
   - FDS 적발률: 99.5% 이상 (이상거래 탐지)
   - NIM: 2.0% 이상
   - ROA: 0.5% 이상
   - BIS 비율: 13% 이상

8. 데이터 모델 설명
   [MST_PRODUCT]  금융 상품 25종 (예금/적금/대출/펀드/보험/카드/파생상품)
   [MST_CUSTOMER] 고객 50명 (개인/법인/소호, VVIP~GENERAL 등급)
   [MST_BRANCH]   영업점 15개 (본점/지점/출장소/디지털지점)

   [FACT_TRANSACTION]
     - 2023-01-01 ~ 2024-12-31, 약 20,000건
     - 계절성: 12/1월 거래 집중, 2월 소폭 감소
     - 이상거래 3%: 이상금액/비정상시간/연속거래/해외거래이상/계좌분산
     - 채널: 모바일앱 38% > 인터넷뱅킹 25% > ATM 18% > 영업점 12% > 자동이체 7%

   [FACT_RISK]
     - 2022-01 ~ 2024-12, 월별 고객 리스크 평가 (50 × 36 = 1,800행)
     - 경제 스트레스 이벤트: 2022-Q4 (금리 급등기), 2023-Q2 (부동산 침체)
     - 스트레스 기간 중 DOWNGRADE 빈도 상승
     - EL = PD(%) / 100 × LGD(%) / 100 × EAD

   [FACT_PERFORMANCE]
     - 2022-01 ~ 2024-12, 월별 지점 성과 (15 × 36 = 540행)
     - 본점/주요지점: 소형 출장소 대비 3-5배 수익
     - Q4 강세(연말 영업), Q1 소폭 약세
     - 순이자이익 = 여신잔액 × NIM(1.5-2.5%) / 12
================================================================
"""


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("금융 리스크 & 포트폴리오 관리 데모 데이터 생성")
    print(f"Output directory: {DATA_DIR}")
    print("=" * 60)

    # --- Master tables ---
    print("\n[1/6] MST_PRODUCT ...")
    products = build_products()
    write_csv("MST_PRODUCT.csv", PRODUCT_FIELDS, [
        {k: fmt(v) for k, v in r.items()} for r in products
    ])

    print("[2/6] MST_CUSTOMER ...")
    customers = build_customers()
    write_csv("MST_CUSTOMER.csv", CUSTOMER_FIELDS, [
        {k: fmt(v) for k, v in r.items()} for r in customers
    ])

    print("[3/6] MST_BRANCH ...")
    branches = build_branches()
    write_csv("MST_BRANCH.csv", BRANCH_FIELDS, [
        {k: fmt(v) for k, v in r.items()} for r in branches
    ])

    # --- Fact tables ---
    print("[4/6] FACT_TRANSACTION (~20,000 rows) ...")
    transactions = build_transactions(customers, products)
    write_csv("FACT_TRANSACTION.csv", TRANSACTION_FIELDS, [
        {k: fmt(v) for k, v in r.items()} for r in transactions
    ])

    print("[5/6] FACT_RISK (50 customers × 36 months) ...")
    risk_rows = build_risk(customers)
    write_csv("FACT_RISK.csv", RISK_FIELDS, [
        {k: fmt(v) for k, v in r.items()} for r in risk_rows
    ])

    print("[6/6] FACT_PERFORMANCE (15 branches × 36 months) ...")
    perf_rows = build_performance()
    write_csv("FACT_PERFORMANCE.csv", PERFORMANCE_FIELDS, [
        {k: fmt(v) for k, v in r.items()} for r in perf_rows
    ])

    # --- Schema + Logic ---
    schema_path = os.path.join(DATA_DIR, "SCHEMA_DEFINITION.json")
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(SCHEMA, f, ensure_ascii=False, indent=2)
    print(f"\n  Wrote SCHEMA_DEFINITION.json  →  {schema_path}")

    logic_path = os.path.join(DATA_DIR, "LOGIC_DOCUMENT.txt")
    with open(logic_path, "w", encoding="utf-8") as f:
        f.write(LOGIC_DOC)
    print(f"  Wrote LOGIC_DOCUMENT.txt      →  {logic_path}")

    print("\n" + "=" * 60)
    print("Done.")
    print("=" * 60)
