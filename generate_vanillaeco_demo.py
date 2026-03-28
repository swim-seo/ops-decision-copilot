"""
에프앤코(바닐라코) 뷰티 이커머스 데모 데이터 생성기
- MST_PRODUCT, MST_CHANNEL, MST_SUPPLIER
- FACT_MONTHLY_SALES, FACT_INVENTORY
- SCHEMA_DEFINITION.json, LOGIC_DOCUMENT.txt
"""

import csv
import json
import os
import random
from datetime import date, timedelta

random.seed(42)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# 마스터 데이터
# ─────────────────────────────────────────────

SUPPLIERS = [
    {"SUPPLIER_ID": "SUP001", "SUPPLIER_NAME": "코스메랩",        "SUPPLIER_TYPE": "원료", "COUNTRY": "KR", "LEAD_TIME_DAYS": 14, "MOQ": 100,   "PAYMENT_TERMS": "NET30"},
    {"SUPPLIER_ID": "SUP002", "SUPPLIER_NAME": "제이솔루션",      "SUPPLIER_TYPE": "원료", "COUNTRY": "KR", "LEAD_TIME_DAYS": 21, "MOQ": 200,   "PAYMENT_TERMS": "NET30"},
    {"SUPPLIER_ID": "SUP003", "SUPPLIER_NAME": "아시아팩",        "SUPPLIER_TYPE": "용기", "COUNTRY": "CN", "LEAD_TIME_DAYS": 45, "MOQ": 5000,  "PAYMENT_TERMS": "NET60"},
    {"SUPPLIER_ID": "SUP004", "SUPPLIER_NAME": "한국화학",        "SUPPLIER_TYPE": "원료", "COUNTRY": "KR", "LEAD_TIME_DAYS":  7, "MOQ":  50,   "PAYMENT_TERMS": "NET30"},
    {"SUPPLIER_ID": "SUP005", "SUPPLIER_NAME": "스킨소스",        "SUPPLIER_TYPE": "원료", "COUNTRY": "KR", "LEAD_TIME_DAYS": 14, "MOQ": 100,   "PAYMENT_TERMS": "NET30"},
    {"SUPPLIER_ID": "SUP006", "SUPPLIER_NAME": "팩코리아",        "SUPPLIER_TYPE": "용기", "COUNTRY": "KR", "LEAD_TIME_DAYS": 30, "MOQ": 1000,  "PAYMENT_TERMS": "NET30"},
    {"SUPPLIER_ID": "SUP007", "SUPPLIER_NAME": "글로벌팩",        "SUPPLIER_TYPE": "용기", "COUNTRY": "CN", "LEAD_TIME_DAYS": 60, "MOQ": 10000, "PAYMENT_TERMS": "NET60"},
    {"SUPPLIER_ID": "SUP008", "SUPPLIER_NAME": "내추럴인그리",    "SUPPLIER_TYPE": "원료", "COUNTRY": "FR", "LEAD_TIME_DAYS": 30, "MOQ":  50,   "PAYMENT_TERMS": "NET45"},
    {"SUPPLIER_ID": "SUP009", "SUPPLIER_NAME": "퍼시픽팩",        "SUPPLIER_TYPE": "용기", "COUNTRY": "KR", "LEAD_TIME_DAYS": 21, "MOQ": 2000,  "PAYMENT_TERMS": "NET30"},
    {"SUPPLIER_ID": "SUP010", "SUPPLIER_NAME": "유로화학",        "SUPPLIER_TYPE": "원료", "COUNTRY": "DE", "LEAD_TIME_DAYS": 35, "MOQ": 100,   "PAYMENT_TERMS": "NET45"},
]

CHANNELS = [
    {"CHANNEL_ID": "CH001", "CHANNEL_NAME": "틱톡샵_KR",    "CHANNEL_TYPE": "온라인",  "REGION": "KR",  "CURRENCY": "KRW", "PLATFORM_FEE_PCT": 5,  "LOCATION": None},
    {"CHANNEL_ID": "CH002", "CHANNEL_NAME": "틱톡샵_SEA",   "CHANNEL_TYPE": "온라인",  "REGION": "SEA", "CURRENCY": "USD", "PLATFORM_FEE_PCT": 8,  "LOCATION": None},
    {"CHANNEL_ID": "CH003", "CHANNEL_NAME": "아마존_US",    "CHANNEL_TYPE": "온라인",  "REGION": "US",  "CURRENCY": "USD", "PLATFORM_FEE_PCT": 15, "LOCATION": None},
    {"CHANNEL_ID": "CH004", "CHANNEL_NAME": "자사몰",        "CHANNEL_TYPE": "온라인",  "REGION": "KR",  "CURRENCY": "KRW", "PLATFORM_FEE_PCT": 0,  "LOCATION": None},
    {"CHANNEL_ID": "CH005", "CHANNEL_NAME": "오프라인_명동", "CHANNEL_TYPE": "오프라인","REGION": "KR",  "CURRENCY": "KRW", "PLATFORM_FEE_PCT": 0,  "LOCATION": "서울 중구 명동"},
    {"CHANNEL_ID": "CH006", "CHANNEL_NAME": "오프라인_성수", "CHANNEL_TYPE": "오프라인","REGION": "KR",  "CURRENCY": "KRW", "PLATFORM_FEE_PCT": 0,  "LOCATION": "서울 성동구 성수동"},
    {"CHANNEL_ID": "CH007", "CHANNEL_NAME": "아마존_SEA",   "CHANNEL_TYPE": "온라인",  "REGION": "SEA", "CURRENCY": "USD", "PLATFORM_FEE_PCT": 15, "LOCATION": None},
]

PRODUCTS = [
    # ── 스킨케어 ──
    {"PRODUCT_ID": "PRD001", "PRODUCT_NAME": "클린잇제로 클렌징밤",      "CATEGORY": "스킨케어", "DEMAND_TYPE": "REORDER",   "SEASONAL_PEAK": None,    "LIFECYCLE_STAGE": "성숙기", "SUPPLIER_ID": "SUP001", "PRICE_KRW": 22000, "PRICE_USD": 17.0, "LAUNCH_DATE": "2020-03-01", "STATUS": "ACTIVE"},
    {"PRODUCT_ID": "PRD002", "PRODUCT_NAME": "선프로텍터 선크림 SPF50+",  "CATEGORY": "스킨케어", "DEMAND_TYPE": "SEASONAL",  "SEASONAL_PEAK": "여름",  "LIFECYCLE_STAGE": "성장기", "SUPPLIER_ID": "SUP004", "PRICE_KRW": 18000, "PRICE_USD": 14.0, "LAUNCH_DATE": "2022-01-01", "STATUS": "ACTIVE"},
    {"PRODUCT_ID": "PRD003", "PRODUCT_NAME": "인텐시브 수분크림",          "CATEGORY": "스킨케어", "DEMAND_TYPE": "SEASONAL",  "SEASONAL_PEAK": "겨울",  "LIFECYCLE_STAGE": "성숙기", "SUPPLIER_ID": "SUP001", "PRICE_KRW": 32000, "PRICE_USD": 25.0, "LAUNCH_DATE": "2019-06-01", "STATUS": "ACTIVE"},
    {"PRODUCT_ID": "PRD004", "PRODUCT_NAME": "퍼스트 토너",                "CATEGORY": "스킨케어", "DEMAND_TYPE": "REORDER",   "SEASONAL_PEAK": None,    "LIFECYCLE_STAGE": "성숙기", "SUPPLIER_ID": "SUP005", "PRICE_KRW": 25000, "PRICE_USD": 19.0, "LAUNCH_DATE": "2018-01-01", "STATUS": "ACTIVE"},
    {"PRODUCT_ID": "PRD005", "PRODUCT_NAME": "앰플 에센스",                "CATEGORY": "스킨케어", "DEMAND_TYPE": "REORDER",   "SEASONAL_PEAK": None,    "LIFECYCLE_STAGE": "성장기", "SUPPLIER_ID": "SUP008", "PRICE_KRW": 45000, "PRICE_USD": 35.0, "LAUNCH_DATE": "2021-09-01", "STATUS": "ACTIVE"},
    {"PRODUCT_ID": "PRD006", "PRODUCT_NAME": "레티놀 리뉴얼 세럼",         "CATEGORY": "스킨케어", "DEMAND_TYPE": "LAUNCH",    "SEASONAL_PEAK": None,    "LIFECYCLE_STAGE": "도입기", "SUPPLIER_ID": "SUP010", "PRICE_KRW": 55000, "PRICE_USD": 42.0, "LAUNCH_DATE": "2025-01-01", "STATUS": "ACTIVE"},
    {"PRODUCT_ID": "PRD007", "PRODUCT_NAME": "아이리페어 크림",            "CATEGORY": "스킨케어", "DEMAND_TYPE": "DECLINING", "SEASONAL_PEAK": None,    "LIFECYCLE_STAGE": "쇠퇴기", "SUPPLIER_ID": "SUP002", "PRICE_KRW": 35000, "PRICE_USD": 27.0, "LAUNCH_DATE": "2017-03-01", "STATUS": "DISCONTINUE"},
    # ── 립 ──
    {"PRODUCT_ID": "PRD008", "PRODUCT_NAME": "벨벳 립틴트",               "CATEGORY": "립",      "DEMAND_TYPE": "REORDER",   "SEASONAL_PEAK": None,    "LIFECYCLE_STAGE": "성숙기", "SUPPLIER_ID": "SUP006", "PRICE_KRW": 12000, "PRICE_USD":  9.0, "LAUNCH_DATE": "2019-04-01", "STATUS": "ACTIVE"},
    {"PRODUCT_ID": "PRD009", "PRODUCT_NAME": "글로우 글로시 립",           "CATEGORY": "립",      "DEMAND_TYPE": "LAUNCH",    "SEASONAL_PEAK": None,    "LIFECYCLE_STAGE": "성장기", "SUPPLIER_ID": "SUP006", "PRICE_KRW": 15000, "PRICE_USD": 12.0, "LAUNCH_DATE": "2024-09-01", "STATUS": "ACTIVE"},
    {"PRODUCT_ID": "PRD010", "PRODUCT_NAME": "모이스처 립밤",              "CATEGORY": "립",      "DEMAND_TYPE": "SEASONAL",  "SEASONAL_PEAK": "겨울",  "LIFECYCLE_STAGE": "성장기", "SUPPLIER_ID": "SUP003", "PRICE_KRW":  8000, "PRICE_USD":  6.0, "LAUNCH_DATE": "2022-11-01", "STATUS": "ACTIVE"},
    {"PRODUCT_ID": "PRD011", "PRODUCT_NAME": "매트 립스틱 클래식",         "CATEGORY": "립",      "DEMAND_TYPE": "DECLINING", "SEASONAL_PEAK": None,    "LIFECYCLE_STAGE": "쇠퇴기", "SUPPLIER_ID": "SUP006", "PRICE_KRW": 14000, "PRICE_USD": 11.0, "LAUNCH_DATE": "2016-05-01", "STATUS": "DISCONTINUE"},
    # ── 아이 ──
    {"PRODUCT_ID": "PRD012", "PRODUCT_NAME": "볼루밍 마스카라",            "CATEGORY": "아이",    "DEMAND_TYPE": "REORDER",   "SEASONAL_PEAK": None,    "LIFECYCLE_STAGE": "성숙기", "SUPPLIER_ID": "SUP009", "PRICE_KRW": 16000, "PRICE_USD": 12.0, "LAUNCH_DATE": "2020-02-01", "STATUS": "ACTIVE"},
    {"PRODUCT_ID": "PRD013", "PRODUCT_NAME": "이지 아이라이너",            "CATEGORY": "아이",    "DEMAND_TYPE": "REORDER",   "SEASONAL_PEAK": None,    "LIFECYCLE_STAGE": "성숙기", "SUPPLIER_ID": "SUP009", "PRICE_KRW": 13000, "PRICE_USD": 10.0, "LAUNCH_DATE": "2019-08-01", "STATUS": "ACTIVE"},
    {"PRODUCT_ID": "PRD014", "PRODUCT_NAME": "데일리 아이섀도우 팔레트",   "CATEGORY": "아이",    "DEMAND_TYPE": "LAUNCH",    "SEASONAL_PEAK": None,    "LIFECYCLE_STAGE": "도입기", "SUPPLIER_ID": "SUP007", "PRICE_KRW": 38000, "PRICE_USD": 29.0, "LAUNCH_DATE": "2025-02-01", "STATUS": "ACTIVE"},
    {"PRODUCT_ID": "PRD015", "PRODUCT_NAME": "내추럴 아이브로우",          "CATEGORY": "아이",    "DEMAND_TYPE": "DECLINING", "SEASONAL_PEAK": None,    "LIFECYCLE_STAGE": "쇠퇴기", "SUPPLIER_ID": "SUP009", "PRICE_KRW": 10000, "PRICE_USD":  8.0, "LAUNCH_DATE": "2015-07-01", "STATUS": "DISCONTINUE"},
    # ── 베이스 ──
    {"PRODUCT_ID": "PRD016", "PRODUCT_NAME": "퍼펙트 커버 쿠션",           "CATEGORY": "베이스",  "DEMAND_TYPE": "REORDER",   "SEASONAL_PEAK": None,    "LIFECYCLE_STAGE": "성숙기", "SUPPLIER_ID": "SUP003", "PRICE_KRW": 28000, "PRICE_USD": 22.0, "LAUNCH_DATE": "2020-05-01", "STATUS": "ACTIVE"},
    {"PRODUCT_ID": "PRD017", "PRODUCT_NAME": "BB크림 올인원",              "CATEGORY": "베이스",  "DEMAND_TYPE": "DECLINING", "SEASONAL_PEAK": None,    "LIFECYCLE_STAGE": "쇠퇴기", "SUPPLIER_ID": "SUP005", "PRICE_KRW": 20000, "PRICE_USD": 15.0, "LAUNCH_DATE": "2016-03-01", "STATUS": "DISCONTINUE"},
    {"PRODUCT_ID": "PRD018", "PRODUCT_NAME": "실크 프라이머",              "CATEGORY": "베이스",  "DEMAND_TYPE": "REORDER",   "SEASONAL_PEAK": None,    "LIFECYCLE_STAGE": "성장기", "SUPPLIER_ID": "SUP005", "PRICE_KRW": 22000, "PRICE_USD": 17.0, "LAUNCH_DATE": "2022-04-01", "STATUS": "ACTIVE"},
    {"PRODUCT_ID": "PRD019", "PRODUCT_NAME": "스킨핏 파운데이션",          "CATEGORY": "베이스",  "DEMAND_TYPE": "LAUNCH",    "SEASONAL_PEAK": None,    "LIFECYCLE_STAGE": "도입기", "SUPPLIER_ID": "SUP007", "PRICE_KRW": 35000, "PRICE_USD": 27.0, "LAUNCH_DATE": "2024-11-01", "STATUS": "ACTIVE"},
    {"PRODUCT_ID": "PRD020", "PRODUCT_NAME": "선쿠션 SPF50+",             "CATEGORY": "베이스",  "DEMAND_TYPE": "SEASONAL",  "SEASONAL_PEAK": "여름",  "LIFECYCLE_STAGE": "성장기", "SUPPLIER_ID": "SUP004", "PRICE_KRW": 24000, "PRICE_USD": 18.0, "LAUNCH_DATE": "2023-03-01", "STATUS": "ACTIVE"},
]

# ─────────────────────────────────────────────
# 수요 모델: 월별 계절 계수 (1=보통)
# ─────────────────────────────────────────────

SEASON_MULT = {
    "여름": {1: 0.30, 2: 0.30, 3: 0.55, 4: 0.85, 5: 1.50, 6: 1.90,
              7: 2.10, 8: 1.70, 9: 0.80, 10: 0.50, 11: 0.30, 12: 0.25},
    "겨울": {1: 1.90, 2: 1.65, 3: 0.80, 4: 0.55, 5: 0.35, 6: 0.30,
              7: 0.30, 8: 0.30, 9: 0.50, 10: 0.85, 11: 1.50, 12: 2.05},
}

REORDER_MULT = {1: 0.90, 2: 0.85, 3: 1.00, 4: 1.05, 5: 1.10, 6: 1.00,
                7: 0.95, 8: 0.90, 9: 1.00, 10: 1.10, 11: 1.20, 12: 1.35}

# LAUNCH: 출시 후 월 경과 → 배율
def launch_mult(months_since_launch: int) -> float:
    curve = {0: 3.0, 1: 2.4, 2: 1.9, 3: 1.6, 4: 1.4, 5: 1.25}
    return curve.get(months_since_launch, 1.10)

# DECLINING: 기준 월부터 매달 감소율 적용
DECLINE_RATE = 0.04   # 월 4% 감소


# 채널별 기본 수요 볼륨 (월 판매량 베이스, 단위: 개)
CHANNEL_BASE_VOLUME = {
    "CH001": 400,   # 틱톡샵_KR – 비교적 높음
    "CH002": 300,   # 틱톡샵_SEA
    "CH003": 250,   # 아마존_US
    "CH004": 350,   # 자사몰
    "CH005": 180,   # 명동 오프라인
    "CH006": 120,   # 성수 오프라인
    "CH007": 200,   # 아마존_SEA
}

# 카테고리별 볼륨 스케일 (립/아이는 단가 낮고 수량 많음)
CATEGORY_SCALE = {"스킨케어": 1.0, "립": 1.5, "아이": 1.3, "베이스": 0.9}

# ─────────────────────────────────────────────
# 날짜 범위: 2024-01 ~ 2025-06 (18개월)
# ─────────────────────────────────────────────

def ym_range():
    """(year, month) 리스트 반환"""
    months = []
    y, m = 2024, 1
    while (y, m) <= (2025, 6):
        months.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months

YM_LIST = ym_range()


def months_since(launch_date_str: str, year: int, month: int) -> int:
    """출시일로부터 경과 월 수 (음수=출시 전)"""
    ld = date.fromisoformat(launch_date_str)
    ref = date(year, month, 1)
    return (ref.year - ld.year) * 12 + (ref.month - ld.month)

# ─────────────────────────────────────────────
# FACT_MONTHLY_SALES 생성
# ─────────────────────────────────────────────

def calc_qty(product: dict, channel_id: str, year: int, month: int) -> int:
    base = CHANNEL_BASE_VOLUME[channel_id] * CATEGORY_SCALE[product["CATEGORY"]]
    ms = months_since(product["LAUNCH_DATE"], year, month)

    if ms < 0:
        return 0  # 출시 전

    dt = product["DEMAND_TYPE"]
    peak = product["SEASONAL_PEAK"]

    if dt == "SEASONAL" and peak:
        mult = SEASON_MULT[peak][month]
    elif dt == "REORDER":
        mult = REORDER_MULT[month]
    elif dt == "LAUNCH":
        mult = launch_mult(ms)
    elif dt == "DECLINING":
        # 기준 시점(2024-01)부터 감소, 이미 쇠퇴 중
        months_declining = max(0, (year - 2022) * 12 + (month - 1))
        mult = max(0.15, 1.0 * ((1 - DECLINE_RATE) ** months_declining))
    else:
        mult = 1.0

    # 노이즈 ±10%
    noise = random.uniform(0.90, 1.10)
    qty = int(base * mult * noise)
    return max(0, qty)


def calc_amount(product: dict, channel_id: str, qty: int) -> float:
    ch = next(c for c in CHANNELS if c["CHANNEL_ID"] == channel_id)
    if ch["CURRENCY"] == "KRW":
        return round(qty * product["PRICE_KRW"], 0)
    else:
        return round(qty * product["PRICE_USD"], 2)

def calc_returns(qty: int, demand_type: str) -> int:
    rates = {"REORDER": 0.015, "SEASONAL": 0.025, "LAUNCH": 0.040, "DECLINING": 0.035}
    rate = rates.get(demand_type, 0.02)
    return int(qty * rate * random.uniform(0.7, 1.3))


sales_rows = []
sale_id = 1
for p in PRODUCTS:
    for ch in CHANNELS:
        for (y, m) in YM_LIST:
            qty = calc_qty(p, ch["CHANNEL_ID"], y, m)
            if qty == 0:
                continue
            amount = calc_amount(p, ch["CHANNEL_ID"], qty)
            returns = calc_returns(qty, p["DEMAND_TYPE"])
            sales_rows.append({
                "SALE_ID": f"SL{sale_id:06d}",
                "PRODUCT_ID": p["PRODUCT_ID"],
                "CHANNEL_ID": ch["CHANNEL_ID"],
                "YEAR_MONTH": f"{y}-{m:02d}",
                "SALES_QTY": qty,
                "SALES_AMOUNT": amount,
                "CURRENCY": next(c["CURRENCY"] for c in CHANNELS if c["CHANNEL_ID"] == ch["CHANNEL_ID"]),
                "RETURN_QTY": returns,
                "NET_SALES_QTY": qty - returns,
            })
            sale_id += 1

# ─────────────────────────────────────────────
# FACT_INVENTORY 생성 (분기말 스냅샷 + 매장/창고별)
# ─────────────────────────────────────────────

# 재고 위치 정의
LOCATIONS = [
    {"LOCATION_ID": "LOC001", "LOCATION_NAME": "인천 물류센터(메인)",  "LOCATION_TYPE": "창고", "REGION": "KR"},
    {"LOCATION_ID": "LOC002", "LOCATION_NAME": "인천 물류센터(온라인)","LOCATION_TYPE": "창고", "REGION": "KR"},
    {"LOCATION_ID": "LOC003", "LOCATION_NAME": "미국 LA 창고",         "LOCATION_TYPE": "창고", "REGION": "US"},
    {"LOCATION_ID": "LOC004", "LOCATION_NAME": "싱가포르 허브",        "LOCATION_TYPE": "창고", "REGION": "SEA"},
    {"LOCATION_ID": "LOC005", "LOCATION_NAME": "명동 매장",            "LOCATION_TYPE": "매장", "REGION": "KR"},
    {"LOCATION_ID": "LOC006", "LOCATION_NAME": "성수 매장",            "LOCATION_TYPE": "매장", "REGION": "KR"},
]

# 스냅샷 날짜: 분기말
SNAPSHOT_DATES = ["2024-03-31","2024-06-30","2024-09-30","2024-12-31","2025-03-31"]

# 안전재고 기준 (수요 유형별 월 커버리지 목표)
SAFETY_WEEKS = {"REORDER": 4, "SEASONAL": 8, "LAUNCH": 6, "DECLINING": 2}

inv_rows = []
inv_id = 1
for p in PRODUCTS:
    dt = p["DEMAND_TYPE"]
    for loc in LOCATIONS:
        for snap in SNAPSHOT_DATES:
            sy, sm, _ = snap.split("-")
            sy, sm = int(sy), int(sm)

            # 해당 위치의 월 평균 수요 추정 (직전 3개월 평균)
            related_channels = []
            if loc["LOCATION_TYPE"] == "창고":
                if loc["REGION"] == "KR":
                    related_channels = ["CH001","CH004"]
                elif loc["REGION"] == "US":
                    related_channels = ["CH003"]
                elif loc["REGION"] == "SEA":
                    related_channels = ["CH002","CH007"]
            else:  # 매장
                related_channels = ["CH005"] if "명동" in loc["LOCATION_NAME"] else ["CH006"]

            avg_monthly = 0
            for ch_id in related_channels:
                for (y, m) in YM_LIST[-3:]:
                    avg_monthly += calc_qty(p, ch_id, y, m)
            avg_monthly = avg_monthly / max(1, len(related_channels) * 3)

            safety_weeks = SAFETY_WEEKS[dt]
            safety_stock = int(avg_monthly * safety_weeks / 4.0)
            reorder_point = int(safety_stock * 1.5)

            # 실재고: 안전재고 ± 랜덤
            if dt == "DECLINING":
                stock_mult = random.uniform(1.0, 2.5)  # 과재고 경향
            elif dt == "SEASONAL":
                # 여름 피크 전(Q1) → 선발주로 높음
                month_to_snap = {3: "Q1", 6: "Q2", 9: "Q3", 12: "Q4"}
                quarter = month_to_snap.get(sm, "Q?")
                peak = p["SEASONAL_PEAK"]
                if (peak == "여름" and quarter == "Q1") or (peak == "겨울" and quarter == "Q3"):
                    stock_mult = random.uniform(2.5, 4.0)  # 시즌 전 선발주
                elif (peak == "여름" and quarter == "Q3") or (peak == "겨울" and quarter == "Q1"):
                    stock_mult = random.uniform(0.2, 0.6)  # 시즌 후 소진
                else:
                    stock_mult = random.uniform(1.0, 1.8)
            elif dt == "LAUNCH":
                ms = months_since(p["LAUNCH_DATE"], sy, sm)
                stock_mult = max(0.3, 2.0 - ms * 0.3)
            else:
                stock_mult = random.uniform(0.8, 1.5)

            stock_qty = max(0, int(safety_stock * stock_mult))

            inv_rows.append({
                "INVENTORY_ID": f"INV{inv_id:06d}",
                "PRODUCT_ID": p["PRODUCT_ID"],
                "LOCATION_ID": loc["LOCATION_ID"],
                "SNAPSHOT_DATE": snap,
                "STOCK_QTY": stock_qty,
                "SAFETY_STOCK_QTY": safety_stock,
                "REORDER_POINT": reorder_point,
                "COVERAGE_WEEKS": round(stock_qty / max(1, avg_monthly / 4.0), 1),
                "STOCK_STATUS": (
                    "OVERSTOCK" if stock_qty > reorder_point * 2.5
                    else "NORMAL" if stock_qty >= reorder_point
                    else "LOW" if stock_qty >= safety_stock
                    else "CRITICAL"
                ),
            })
            inv_id += 1


# ─────────────────────────────────────────────
# CSV 저장 헬퍼
# ─────────────────────────────────────────────

def write_csv(filename: str, rows: list[dict]):
    if not rows:
        print(f"  [SKIP] {filename} - 데이터 없음")
        return
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"  [OK] {filename} ({len(rows):,}행) → {path}")


# ─────────────────────────────────────────────
# SCHEMA_DEFINITION.json
# ─────────────────────────────────────────────

SCHEMA = {
    "schema_version": "1.0",
    "domain": "뷰티 이커머스 (에프앤코 / 바닐라코)",
    "tables": {
        "MST_SUPPLIER": {
            "description": "원료·용기 공급업체 마스터",
            "primary_key": "SUPPLIER_ID",
            "columns": {
                "SUPPLIER_ID":    {"type": "VARCHAR(6)",  "nullable": False, "example": "SUP001"},
                "SUPPLIER_NAME":  {"type": "VARCHAR(50)", "nullable": False, "example": "코스메랩"},
                "SUPPLIER_TYPE":  {"type": "VARCHAR(10)", "nullable": False, "enum": ["원료", "용기"]},
                "COUNTRY":        {"type": "CHAR(2)",     "nullable": False, "example": "KR"},
                "LEAD_TIME_DAYS": {"type": "INTEGER",     "nullable": False, "description": "발주~납품 소요일"},
                "MOQ":            {"type": "INTEGER",     "nullable": False, "description": "최소주문수량"},
                "PAYMENT_TERMS":  {"type": "VARCHAR(10)", "nullable": True,  "example": "NET30"},
            }
        },
        "MST_CHANNEL": {
            "description": "판매 채널 마스터 (온·오프라인, 글로벌)",
            "primary_key": "CHANNEL_ID",
            "columns": {
                "CHANNEL_ID":        {"type": "VARCHAR(5)",  "nullable": False, "example": "CH001"},
                "CHANNEL_NAME":      {"type": "VARCHAR(30)", "nullable": False, "example": "틱톡샵_KR"},
                "CHANNEL_TYPE":      {"type": "VARCHAR(10)", "nullable": False, "enum": ["온라인", "오프라인"]},
                "REGION":            {"type": "VARCHAR(5)",  "nullable": False, "enum": ["KR", "US", "SEA"]},
                "CURRENCY":          {"type": "CHAR(3)",     "nullable": False, "enum": ["KRW", "USD"]},
                "PLATFORM_FEE_PCT":  {"type": "DECIMAL(4,1)","nullable": False, "description": "플랫폼 수수료율(%)"},
                "LOCATION":          {"type": "VARCHAR(50)", "nullable": True,  "description": "오프라인 주소"},
            }
        },
        "MST_PRODUCT": {
            "description": "상품 마스터 (수요 유형·라이프사이클 포함)",
            "primary_key": "PRODUCT_ID",
            "foreign_keys": {"SUPPLIER_ID": "MST_SUPPLIER.SUPPLIER_ID"},
            "columns": {
                "PRODUCT_ID":      {"type": "VARCHAR(6)",  "nullable": False, "example": "PRD001"},
                "PRODUCT_NAME":    {"type": "VARCHAR(60)", "nullable": False},
                "CATEGORY":        {"type": "VARCHAR(10)", "nullable": False, "enum": ["스킨케어", "립", "아이", "베이스"]},
                "DEMAND_TYPE":     {"type": "VARCHAR(10)", "nullable": False, "enum": ["SEASONAL", "REORDER", "LAUNCH", "DECLINING"],
                                    "description": "수요 유형 - 재고 전략의 핵심 분류"},
                "SEASONAL_PEAK":   {"type": "VARCHAR(5)",  "nullable": True,  "enum": ["여름", "겨울", None]},
                "LIFECYCLE_STAGE": {"type": "VARCHAR(8)",  "nullable": False, "enum": ["도입기", "성장기", "성숙기", "쇠퇴기"]},
                "SUPPLIER_ID":     {"type": "VARCHAR(6)",  "nullable": False, "fk": "MST_SUPPLIER.SUPPLIER_ID"},
                "PRICE_KRW":       {"type": "INTEGER",     "nullable": False},
                "PRICE_USD":       {"type": "DECIMAL(8,2)","nullable": False},
                "LAUNCH_DATE":     {"type": "DATE",        "nullable": False},
                "STATUS":          {"type": "VARCHAR(12)", "nullable": False, "enum": ["ACTIVE", "DISCONTINUE"]},
            }
        },
        "FACT_MONTHLY_SALES": {
            "description": "채널별 월간 판매 실적 팩트",
            "primary_key": "SALE_ID",
            "foreign_keys": {
                "PRODUCT_ID": "MST_PRODUCT.PRODUCT_ID",
                "CHANNEL_ID": "MST_CHANNEL.CHANNEL_ID",
            },
            "columns": {
                "SALE_ID":        {"type": "VARCHAR(9)",   "nullable": False},
                "PRODUCT_ID":     {"type": "VARCHAR(6)",   "nullable": False, "fk": "MST_PRODUCT.PRODUCT_ID"},
                "CHANNEL_ID":     {"type": "VARCHAR(5)",   "nullable": False, "fk": "MST_CHANNEL.CHANNEL_ID"},
                "YEAR_MONTH":     {"type": "CHAR(7)",      "nullable": False, "example": "2024-01"},
                "SALES_QTY":      {"type": "INTEGER",      "nullable": False},
                "SALES_AMOUNT":   {"type": "DECIMAL(14,2)","nullable": False},
                "CURRENCY":       {"type": "CHAR(3)",      "nullable": False},
                "RETURN_QTY":     {"type": "INTEGER",      "nullable": False},
                "NET_SALES_QTY":  {"type": "INTEGER",      "nullable": False},
            }
        },
        "FACT_INVENTORY": {
            "description": "매장·창고별 재고 현황 스냅샷 (분기말 기준)",
            "primary_key": "INVENTORY_ID",
            "foreign_keys": {"PRODUCT_ID": "MST_PRODUCT.PRODUCT_ID"},
            "columns": {
                "INVENTORY_ID":     {"type": "VARCHAR(9)",   "nullable": False},
                "PRODUCT_ID":       {"type": "VARCHAR(6)",   "nullable": False, "fk": "MST_PRODUCT.PRODUCT_ID"},
                "LOCATION_ID":      {"type": "VARCHAR(6)",   "nullable": False, "description": "창고/매장 코드"},
                "SNAPSHOT_DATE":    {"type": "DATE",         "nullable": False},
                "STOCK_QTY":        {"type": "INTEGER",      "nullable": False},
                "SAFETY_STOCK_QTY": {"type": "INTEGER",      "nullable": False},
                "REORDER_POINT":    {"type": "INTEGER",      "nullable": False},
                "COVERAGE_WEEKS":   {"type": "DECIMAL(5,1)", "nullable": False, "description": "현재고 ÷ 주평균수요"},
                "STOCK_STATUS":     {"type": "VARCHAR(10)",  "nullable": False, "enum": ["OVERSTOCK","NORMAL","LOW","CRITICAL"]},
            }
        },
        "MST_LOCATION": {
            "description": "창고·매장 위치 마스터 (FACT_INVENTORY 참조)",
            "primary_key": "LOCATION_ID",
            "columns": {
                "LOCATION_ID":   {"type": "VARCHAR(6)",  "nullable": False},
                "LOCATION_NAME": {"type": "VARCHAR(30)", "nullable": False},
                "LOCATION_TYPE": {"type": "VARCHAR(5)",  "nullable": False, "enum": ["창고", "매장"]},
                "REGION":        {"type": "VARCHAR(5)",  "nullable": False, "enum": ["KR", "US", "SEA"]},
            }
        }
    },
    "relationships": [
        {"from": "MST_PRODUCT.SUPPLIER_ID",      "to": "MST_SUPPLIER.SUPPLIER_ID",  "type": "N:1"},
        {"from": "FACT_MONTHLY_SALES.PRODUCT_ID","to": "MST_PRODUCT.PRODUCT_ID",    "type": "N:1"},
        {"from": "FACT_MONTHLY_SALES.CHANNEL_ID","to": "MST_CHANNEL.CHANNEL_ID",    "type": "N:1"},
        {"from": "FACT_INVENTORY.PRODUCT_ID",    "to": "MST_PRODUCT.PRODUCT_ID",    "type": "N:1"},
        {"from": "FACT_INVENTORY.LOCATION_ID",   "to": "MST_LOCATION.LOCATION_ID",  "type": "N:1"},
    ]
}


# ─────────────────────────────────────────────
# LOGIC_DOCUMENT.txt
# ─────────────────────────────────────────────

LOGIC_DOC = """
================================================================
에프앤코(바닐라코) 수요 유형별 재고 관리 전략 문서
작성 기준: 2025년 상반기 운영 정책
================================================================

1. SEASONAL (계절성 수요)
────────────────────────────────────────
해당 상품: 선프로텍터 선크림 SPF50+, 선쿠션 SPF50+ (여름 피크)
           인텐시브 수분크림, 모이스처 립밤 (겨울 피크)

▶ 핵심 원칙: 피크 전 충분한 선발주, 시즌 후 잔재고 최소화

[선발주 기준]
 - 피크 시즌 6주 전: 예상 피크 수요량의 100% 발주 확정
 - 피크 시즌 3주 전: 부족분 긴급 추가 발주 가능 (MOQ 미적용 협의)
 - 시즌 종료 4주 전: 추가 발주 중단, 잔재고 소진 집중

[재고 목표 Coverage]
 - 피크 시즌 前 8주: 최소 8주치 보유 (안전재고 = 예상 월판매량 × 2)
 - 피크 시즌 中: 4주치 유지 (주간 모니터링)
 - 비수기: 2주치 이하로 유지 (보관비 절감)

[채널별 배분]
 - 여름 상품: 틱톡샵_KR·SEA에 60% 우선 배정 (바이럴 효과)
 - 겨울 상품: 자사몰·오프라인 매장에 50% 배정 (체험 구매 유도)

[KPI]
 - 피크 재고 소진율 > 90% (시즌 종료 후 4주 기준)
 - 품절로 인한 기회손실 < 5%


2. REORDER (지속 재구매형 수요)
────────────────────────────────────────
해당 상품: 클린잇제로 클렌징밤, 퍼스트 토너, 앰플 에센스,
           벨벳 립틴트, 볼루밍 마스카라, 이지 아이라이너,
           퍼펙트 커버 쿠션, 실크 프라이머

▶ 핵심 원칙: 정기 발주 사이클 유지, 품절 방지가 최우선

[발주 사이클]
 - 발주 주기: 4주 (월 1회 정기 발주)
 - 리드타임 버퍼: 공급업체 리드타임 + 1주 여유
 - 재주문점(ROP) = 일평균수요 × (리드타임 + 안전재고일수)

[안전재고 설정]
 - 안전재고 = 4주치 수요량
 - 서비스 수준 목표: 98% (연간 재고소진 발생 < 8회)

[자동 발주 트리거]
 - 재고 < ROP → 자동 발주 알림 생성
 - 재고 < 안전재고 → 긴급 발주 + 담당자 에스컬레이션

[채널 우선순위]
 1순위: 자사몰 (마진 최고)
 2순위: 틱톡샵 (볼륨)
 3순위: 오프라인 매장 (브랜드 이미지)
 4순위: 아마존 (글로벌 확장)

[KPI]
 - 재고 회전율: 연 8회 이상
 - 품절률: < 2%


3. LAUNCH (신제품 출시형 수요)
────────────────────────────────────────
해당 상품: 레티놀 리뉴얼 세럼 (2025.01 출시)
           데일리 아이섀도우 팔레트 (2025.02 출시)
           스킨핏 파운데이션 (2024.11 출시)
           글로우 글로시 립 (2024.09 출시)

▶ 핵심 원칙: 출시 초반 공급 불안을 최소화, 3개월 후 정상 사이클 전환

[출시 전 준비]
 - 출시 D-8주: 초도물량 발주 확정 (예상 월판매량 × 3배)
 - 출시 D-2주: 채널별 입고 완료
 - 출시 D-Day: 재고 상태 실시간 모니터링 시작

[출시 후 재고 운영]
 - 1개월차: 일별 판매 모니터링, 수요 예측 재산정
 - 2~3개월차: 예측 대비 ±30% 이탈 시 긴급 발주/프로모션
 - 4개월차~: REORDER 상품과 동일한 정기 발주 사이클 전환

[채널 출시 전략]
 - 출시 1~2주: 틱톡샵 + 자사몰 우선 (화제성 극대화)
 - 출시 3~4주: 아마존·오프라인 확대
 - 2개월차~: 전채널 균등 공급

[리스크 관리]
 - 예상 초과 판매 시: 백오더 수용 기간 최대 2주
 - 예상 미달 판매 시: 3개월차에 프로모션 번들 판매로 소진

[KPI]
 - 출시 1개월 품절률: < 10%
 - 출시 6개월 내 재고 정상화율: > 85%


4. DECLINING (수요 감소형 / 단종 예정)
────────────────────────────────────────
해당 상품: 아이리페어 크림, 매트 립스틱 클래식,
           내추럴 아이브로우, BB크림 올인원

▶ 핵심 원칙: 신규 발주 최소화, 잔재고 소진 후 단종

[발주 중단 조건]
 - 월판매량 < 최소 발주량(MOQ) 도달 시 신규 발주 중단
 - 잔재고 > 6개월치: 즉시 발주 중단 + 소진 계획 수립

[재고 소진 전략]
 - 1단계: 채널별 프로모션 (번들, 증정 이벤트)
 - 2단계: 할인 판매 (최대 40% DC까지 허용)
 - 3단계: B2B 처분 (협력사·기부·렌탈 스튜디오 공급)
 - 4단계: 폐기 (원가 손실 처리, CFO 승인 필요)

[채널 우선순위]
 - 자사몰 프로모션 → 오프라인 매장 할인 → 아마존 Last Deal

[안전재고 설정]
 - 안전재고 = 2주치 (최소한만 유지)
 - 신규 발주 시 최소 수량(MOQ)만 주문

[KPI]
 - 폐기율: < 5% (잔재고 대비)
 - 단종 목표일 준수율: > 90%
 - 잔재고 소진 목표: 단종 선언 후 6개월 이내 95% 소진


================================================================
부록: 재고 위험 등급 정의
================================================================

 CRITICAL  : 현재고 < 안전재고        → 즉시 긴급 발주
 LOW        : 안전재고 ≤ 재고 < ROP   → 다음 정기 발주 앞당김
 NORMAL     : ROP ≤ 재고 < ROP × 2.5  → 정상 운영
 OVERSTOCK  : 재고 ≥ ROP × 2.5        → 프로모션·채널 이동 검토

================================================================
"""


# ─────────────────────────────────────────────
# 실행
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n[ 에프앤코(바닐라코) 데모 데이터 생성 ]\n")

    write_csv("MST_SUPPLIER.csv", SUPPLIERS)
    write_csv("MST_CHANNEL.csv",  CHANNELS)
    write_csv("MST_PRODUCT.csv",  PRODUCTS)
    write_csv("MST_LOCATION.csv", LOCATIONS)
    write_csv("FACT_MONTHLY_SALES.csv", sales_rows)
    write_csv("FACT_INVENTORY.csv",     inv_rows)

    schema_path = os.path.join(DATA_DIR, "SCHEMA_DEFINITION.json")
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(SCHEMA, f, ensure_ascii=False, indent=2)
    print(f"  [OK] SCHEMA_DEFINITION.json → {schema_path}")

    logic_path = os.path.join(DATA_DIR, "LOGIC_DOCUMENT.txt")
    with open(logic_path, "w", encoding="utf-8") as f:
        f.write(LOGIC_DOC.strip())
    print(f"  [OK] LOGIC_DOCUMENT.txt → {logic_path}")

    print(f"\n총 판매 레코드: {len(sales_rows):,}건")
    print(f"총 재고 레코드: {len(inv_rows):,}건")
    print("\n완료!")
