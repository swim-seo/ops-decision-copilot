"""[역할] 뷰티 이커머스 데모 데이터 생성기 (data/beauty)

마스터 테이블(MST_*)을 진실의 원천으로 삼아 팩트 테이블(FACT_*)을 생성합니다.
핵심 원칙은 "문서와 데이터의 일치" 입니다 — data/beauty/LOGIC_DOCUMENT.txt 에
문서화된 운영 규칙을 데이터가 실제로 만족하도록 계산하므로, RAG/GraphRAG 답변을
문서 기준으로 검증할 수 있습니다.

기존 data/beauty CSV 는 손으로 작성되어 다음 결함이 있었습니다(이 스크립트로 해소):
  - 제품 20개 중 판매 실적이 PRD001 하나뿐 → 제품 비교·랭킹 질문이 성립 불가
  - FACT_INVENTORY.LOCATION_ID(LOC00x) 가 MST_WAREHOUSE(WH00x) 와 불일치 → 고아 FK
  - MST_PRODUCT 10개가 존재하지 않는 공급사(SUP006~010) 참조

LOGIC_DOCUMENT.txt 의 정량 규칙:
  일평균 판매량 = 월 판매량 / 30
  안전재고      = 일평균 판매량 × 리드타임 × 1.5
  재주문점(ROP) = 일평균 판매량 × 리드타임 + 안전재고
  CRITICAL     : 가용재고 < 안전재고 × 0.5
  WARNING      : 가용재고 < 안전재고
  DEADSTOCK    : 단종 제품의 잔여 재고
  여름(6~8월)  : 선케어 3~5배 / 겨울(11~2월): 보습 2~3배

시드를 고정했으므로 실행마다 동일한 결과가 나옵니다(재현 가능).

사용법:
    python scripts/generate_beauty.py              # data/beauty 에 생성
    python scripts/generate_beauty.py --dry-run    # 검증만, 파일 미기록
"""
from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

SEED = 20260730
PERIOD_START = (2025, 1)
PERIOD_MONTHS = 18  # 2025-01 ~ 2026-06

DEFAULT_DIR = Path(__file__).resolve().parents[1] / "data" / "beauty"

# ── 판매량 모델 파라미터 ────────────────────────────────────────────────
# 생애주기 단계별 기준 수요(월, 개)와 월 성장률
LIFECYCLE_PROFILE: Dict[str, Tuple[int, float]] = {
    "도입기": (110, 0.11),
    "성장기": (300, 0.035),
    "성숙기": (450, 0.0),
    "쇠퇴기": (240, -0.06),
}

# 채널별 기본 판매 비중
CHANNEL_SHARE: Dict[str, float] = {
    "CH001": 0.34,  # 올리브영
    "CH002": 0.27,  # 자사몰
    "CH003": 0.22,  # 쿠팡
    "CH004": 0.11,  # 무신사
    "CH005": 0.06,  # 면세점
}
# 무신사는 색조 중심, 면세점은 스킨케어·베이스 중심으로만 취급
CHANNEL_CATEGORIES: Dict[str, Optional[set]] = {
    "CH001": None,
    "CH002": None,
    "CH003": None,
    "CH004": {"립", "아이", "베이스"},
    "CH005": {"스킨케어", "베이스"},
}

SUMMER_MONTHS = {6, 7, 8}
SUMMER_SHOULDER = {5, 9}
WINTER_MONTHS = {11, 12, 1, 2}
WINTER_SHOULDER = {10, 3}

RETURN_BASE_RATE = 0.021
RETURN_REASONS = [
    ("단순변심", 0.50),
    ("품질불량", 0.19),
    ("배송파손", 0.15),
    ("오배송", 0.11),
    ("기타", 0.05),
]

# ── 의도적으로 심는 시나리오 ────────────────────────────────────────────
# 데모에서 "AI가 발견해야 하는 문제"가 데이터에 실제로 존재하도록 만든다.
QUALITY_ISSUE_PRODUCT = "PRD016"        # 퍼펙트 커버 쿠션
QUALITY_ISSUE_FROM = (2026, 1)          # 이 달부터 품질불량 반품률 급증
QUALITY_ISSUE_RATE = 0.12

STOCKOUT_PRODUCT = "PRD002"             # 선프로텍터 선크림 — 2026 사전발주 누락
STOCKOUT_MONTHS = {(2026, 5), (2026, 6)}
MISSED_PREORDER_YEAR = 2026             # 이 해 3월 선케어 사전발주를 누락시킨다

FAST_GROWTH_PRODUCT = "PRD006"          # 레티놀 세럼 — 급성장으로 재고가 계속 빈약

DISCONTINUE_LAST_SALE: Dict[str, Tuple[int, int]] = {
    "PRD007": (2025, 8),
    "PRD011": (2025, 11),
    "PRD015": (2025, 6),
    "PRD017": (2026, 2),
}


# ── 유틸 ────────────────────────────────────────────────────────────────
def month_sequence(start: Tuple[int, int], count: int) -> List[Tuple[int, int]]:
    year, month = start
    out: List[Tuple[int, int]] = []
    for _ in range(count):
        out.append((year, month))
        month += 1
        if month > 12:
            year, month = year + 1, 1
    return out


def month_key(ym: Tuple[int, int]) -> str:
    return f"{ym[0]:04d}-{ym[1]:02d}"


def month_end(ym: Tuple[int, int]) -> date:
    year, month = ym
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def month_index(ym: Tuple[int, int]) -> int:
    return ym[0] * 12 + ym[1]


def read_csv(path: Path) -> List[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[dict], columns: List[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def weighted_choice(rng: random.Random, options: List[Tuple[str, float]]) -> str:
    total = sum(w for _, w in options)
    threshold = rng.random() * total
    acc = 0.0
    for value, weight in options:
        acc += weight
        if threshold <= acc:
            return value
    return options[-1][0]


# ── 마스터 로딩 ─────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Masters:
    products: List[dict]
    channels: List[dict]
    suppliers: List[dict]
    warehouses: List[dict]
    promotions: List[dict]

    @property
    def supplier_by_id(self) -> Dict[str, dict]:
        return {s["SUPPLIER_ID"]: s for s in self.suppliers}

    @property
    def product_by_id(self) -> Dict[str, dict]:
        return {p["PRODUCT_ID"]: p for p in self.products}


def load_masters(base: Path) -> Masters:
    return Masters(
        products=read_csv(base / "MST_PRODUCT.csv"),
        channels=read_csv(base / "MST_CHANNEL.csv"),
        suppliers=read_csv(base / "MST_SUPPLIER.csv"),
        warehouses=read_csv(base / "MST_WAREHOUSE.csv"),
        promotions=read_csv(base / "MST_PROMOTION.csv"),
    )


# ── 판매량 모델 ─────────────────────────────────────────────────────────
def seasonal_multiplier(product: dict, ym: Tuple[int, int], rng: random.Random) -> float:
    """LOGIC_DOCUMENT 의 시즌 배수를 적용합니다."""
    peak = (product.get("SEASONAL_PEAK") or "").strip()
    month = ym[1]

    if peak == "여름":
        if month in SUMMER_MONTHS:
            return rng.uniform(3.0, 5.0)
        if month in SUMMER_SHOULDER:
            return rng.uniform(1.4, 1.8)
        return rng.uniform(0.5, 0.7)

    if peak == "겨울":
        if month in WINTER_MONTHS:
            return rng.uniform(2.0, 3.0)
        if month in WINTER_SHOULDER:
            return rng.uniform(1.3, 1.5)
        return rng.uniform(0.5, 0.7)

    # 비시즌 상품도 완만한 연간 파동을 가진다.
    return 1.0 + 0.08 * math.sin((month - 3) / 12 * 2 * math.pi)


def launch_ramp(product: dict, ym: Tuple[int, int]) -> float:
    """출시 직후 3개월은 서서히 올라옵니다. 출시 전이면 0."""
    launch = date.fromisoformat(product["LAUNCH_DATE"])
    delta = month_index(ym) - (launch.year * 12 + launch.month)
    if delta < 0:
        return 0.0
    return {0: 0.45, 1: 0.7, 2: 0.9}.get(delta, 1.0)


def discontinue_factor(product_id: str, ym: Tuple[int, int]) -> float:
    """단종 제품은 판매 종료 4개월 전부터 감소하고 종료 후에는 0."""
    last = DISCONTINUE_LAST_SALE.get(product_id)
    if last is None:
        return 1.0
    remaining = month_index(last) - month_index(ym)
    if remaining < 0:
        return 0.0
    if remaining >= 4:
        return 1.0
    return 0.25 * (remaining + 1)


def promo_lift(promotions: List[dict], channel_id: str, category: str,
               ym: Tuple[int, int]) -> Tuple[float, List[str]]:
    """해당 월·채널에 걸린 프로모션의 판매 상승 배수와 프로모션 ID 목록."""
    lift = 1.0
    hits: List[str] = []
    first_day = month_end(ym).replace(day=1)

    for promo in promotions:
        if promo["CHANNEL_ID"] != channel_id:
            continue
        if promo["TARGET_CATEGORY"] not in ("전체", category):
            continue

        start = date.fromisoformat(promo["START_DATE"])
        end = date.fromisoformat(promo["END_DATE"])
        overlap_start = max(start, first_day)
        overlap_end = min(end, month_end(ym))
        if overlap_end < overlap_start:
            continue

        coverage = min(1.0, ((overlap_end - overlap_start).days + 1) / 30)
        # 할인율이 클수록, 기간이 길수록 상승폭이 크다.
        lift += 2.2 * float(promo["DISCOUNT_RATE"]) * coverage
        hits.append(promo["PROMOTION_ID"])

    return lift, hits


def base_demand(product: dict, ym: Tuple[int, int]) -> float:
    stage = product["LIFECYCLE_STAGE"]
    base, growth = LIFECYCLE_PROFILE.get(stage, (300, 0.0))
    elapsed = month_index(ym) - month_index(PERIOD_START)
    price = float(product["PRICE_KRW"])
    # 저가 상품이 더 많이 팔린다(가격 탄력성 근사).
    price_factor = min(1.8, max(0.6, (20000 / price) ** 0.5))
    return base * price_factor * ((1 + growth) ** elapsed)


SalesResult = Tuple[
    List[dict],
    Dict[Tuple[str, Tuple[int, int]], int],
    Dict[Tuple[str, str, Tuple[int, int]], List[str]],
]


def build_sales(masters: Masters, months: List[Tuple[int, int]],
                rng: random.Random) -> SalesResult:
    """FACT_MONTHLY_SALES 생성. 제품별 월 합계와 프로모션 매칭도 함께 반환."""
    rows: List[dict] = []
    monthly_total: Dict[Tuple[str, Tuple[int, int]], int] = {}
    promo_hits: Dict[Tuple[str, str, Tuple[int, int]], List[str]] = {}
    seq = 0

    for product in masters.products:
        pid = product["PRODUCT_ID"]
        category = product["CATEGORY"]
        price_krw = int(product["PRICE_KRW"])
        price_usd = int(product["PRICE_USD"])

        for ym in months:
            ramp = launch_ramp(product, ym)
            disc = discontinue_factor(pid, ym)
            if ramp == 0.0 or disc == 0.0:
                continue

            demand = base_demand(product, ym) * ramp * disc
            demand *= seasonal_multiplier(product, ym, rng)

            total_qty = 0
            for channel in masters.channels:
                cid = channel["CHANNEL_ID"]
                allowed = CHANNEL_CATEGORIES.get(cid)
                if allowed is not None and category not in allowed:
                    continue

                lift, hits = promo_lift(masters.promotions, cid, category, ym)
                qty = demand * CHANNEL_SHARE.get(cid, 0.0) * lift * rng.uniform(0.88, 1.12)

                # 결품 시나리오: 재고가 없어 판매가 눌린다.
                if pid == STOCKOUT_PRODUCT and ym in STOCKOUT_MONTHS:
                    qty *= 0.35

                qty_int = int(round(qty))
                if qty_int <= 0:
                    continue

                if pid == QUALITY_ISSUE_PRODUCT and month_index(ym) >= month_index(QUALITY_ISSUE_FROM):
                    return_rate = QUALITY_ISSUE_RATE
                elif pid in DISCONTINUE_LAST_SALE:
                    return_rate = 0.03
                else:
                    return_rate = RETURN_BASE_RATE
                return_qty = int(round(qty_int * return_rate * rng.uniform(0.8, 1.2)))

                is_duty_free = cid == "CH005"
                unit_price = price_usd if is_duty_free else price_krw
                # 프로모션 기간에는 실판매가가 낮아진다.
                realized = unit_price * (1 - 0.5 * (lift - 1) / 2.2)

                seq += 1
                rows.append({
                    "SALE_ID": f"SL{seq:06d}",
                    "PRODUCT_ID": pid,
                    "CHANNEL_ID": cid,
                    "YEAR_MONTH": month_key(ym),
                    "SALES_QTY": qty_int,
                    "SALES_AMOUNT": int(round(qty_int * realized)),
                    "CURRENCY": "USD" if is_duty_free else "KRW",
                    "RETURN_QTY": return_qty,
                    "NET_SALES_QTY": qty_int - return_qty,
                })
                total_qty += qty_int
                if hits:
                    promo_hits[(pid, cid, ym)] = hits

            if total_qty:
                monthly_total[(pid, ym)] = total_qty

    return rows, monthly_total, promo_hits


# ── 재고 ────────────────────────────────────────────────────────────────
def warehouse_allocation(product: dict, warehouses: List[dict]) -> List[Tuple[str, float]]:
    """제품별 창고 배분. 면세 취급 카테고리는 보세창고(WH003)에도 재고를 둔다."""
    alloc = ([("WH001", 0.55), ("WH002", 0.33), ("WH003", 0.12)]
             if product["CATEGORY"] in {"스킨케어", "베이스"}
             else [("WH001", 0.6), ("WH002", 0.4)])
    have = {w["WAREHOUSE_ID"] for w in warehouses}
    return [(wid, share) for wid, share in alloc if wid in have]


def stock_status(stock: int, safety: int) -> str:
    """LOGIC_DOCUMENT 의 재고 상태 판정 규칙."""
    if safety <= 0:
        return "DEADSTOCK" if stock > 0 else "NORMAL"
    if stock < safety * 0.5:
        return "CRITICAL"
    if stock < safety:
        return "WARNING"
    return "NORMAL"


def build_inventory(masters: Masters, months: List[Tuple[int, int]],
                    monthly_total: Dict[Tuple[str, Tuple[int, int]], int],
                    rng: random.Random) -> List[dict]:
    rows: List[dict] = []
    suppliers = masters.supplier_by_id
    seq = 0

    for product in masters.products:
        pid = product["PRODUCT_ID"]
        lead = int(suppliers[product["SUPPLIER_ID"]]["LEAD_TIME_DAYS"])
        alloc = warehouse_allocation(product, masters.warehouses)
        launch = date.fromisoformat(product["LAUNCH_DATE"])

        for ym in months:
            if month_index(ym) < launch.year * 12 + launch.month:
                continue

            sold = monthly_total.get((pid, ym), 0)
            for wid, share in alloc:
                daily_avg = (sold * share) / 30
                safety = int(round(daily_avg * lead * 1.5))
                rop = int(round(daily_avg * lead + safety))

                if sold == 0:
                    # 단종 후 남은 잔여 재고 — 소진되지 않는 악성재고
                    stock = int(round(200 * share * rng.uniform(0.7, 1.3)))
                elif pid == STOCKOUT_PRODUCT and ym in STOCKOUT_MONTHS:
                    stock = int(round(safety * rng.uniform(0.15, 0.4)))   # CRITICAL 유발
                elif pid == FAST_GROWTH_PRODUCT:
                    stock = int(round(safety * rng.uniform(0.4, 0.95)))   # 성장 속도를 못 따라감
                else:
                    stock = int(round(safety * rng.uniform(0.85, 2.1)))

                seq += 1
                rows.append({
                    "INVENTORY_ID": f"INV{seq:06d}",
                    "PRODUCT_ID": pid,
                    "WAREHOUSE_ID": wid,
                    "SNAPSHOT_DATE": month_end(ym).isoformat(),
                    "STOCK_QTY": stock,
                    "SAFETY_STOCK_QTY": safety,
                    "REORDER_POINT": rop,
                    "COVERAGE_WEEKS": round(stock / (daily_avg * 7), 1) if daily_avg > 0 else 0.0,
                    "STOCK_STATUS": stock_status(stock, safety),
                })

    return rows


# ── 발주 ────────────────────────────────────────────────────────────────
def build_orders(masters: Masters, inventory: List[dict], rng: random.Random) -> List[dict]:
    """재고가 ROP 이하로 떨어진 시점에 발주가 발생합니다(문서의 발주 트리거)."""
    rows: List[dict] = []
    suppliers = masters.supplier_by_id
    products = masters.product_by_id
    period_first = date(PERIOD_START[0], PERIOD_START[1], 1)
    last_day = month_end(month_sequence(PERIOD_START, PERIOD_MONTHS)[-1])

    for inv in inventory:
        if inv["WAREHOUSE_ID"] != "WH001":       # 발주는 주센터 기준으로만 집계
            continue
        if inv["STOCK_STATUS"] == "DEADSTOCK" or inv["STOCK_QTY"] > inv["REORDER_POINT"]:
            continue

        product = products[inv["PRODUCT_ID"]]
        supplier = suppliers[product["SUPPLIER_ID"]]
        lead = int(supplier["LEAD_TIME_DAYS"])

        order_date = date.fromisoformat(inv["SNAPSHOT_DATE"]) + timedelta(days=3)
        need = max(0, inv["SAFETY_STOCK_QTY"] * 2 - inv["STOCK_QTY"])
        qty = max(int(supplier["MOQ"]), int(math.ceil(need / 100.0) * 100))

        expected = order_date + timedelta(days=lead)
        delayed = supplier["COUNTRY"] != "KR" and rng.random() < 0.35
        if delayed:
            expected += timedelta(days=rng.randint(5, 9))

        if expected <= last_day:
            status = "DELAYED" if delayed else "DELIVERED"
        elif order_date <= last_day:
            status = "IN_TRANSIT"
        else:
            continue

        rows.append({
            "ORDER_ID": "",
            "PRODUCT_ID": inv["PRODUCT_ID"],
            "SUPPLIER_ID": supplier["SUPPLIER_ID"],
            "ORDER_DATE": order_date.isoformat(),
            "EXPECTED_DATE": expected.isoformat(),
            "QTY": qty,
            "UNIT_COST": int(round(int(product["PRICE_KRW"]) * rng.uniform(0.35, 0.45) / 100) * 100),
            "STATUS": status,
        })

    # 시즌 사전발주 — 여름 선케어는 3월, 겨울 보습은 9월(문서 규칙).
    # MISSED_PREORDER_YEAR 의 선케어 사전발주는 의도적으로 누락시켜 결품 원인을 만든다.
    for product in masters.products:
        peak = (product.get("SEASONAL_PEAK") or "").strip()
        if not peak:
            continue
        supplier = suppliers[product["SUPPLIER_ID"]]
        for year in {PERIOD_START[0], last_day.year}:
            if peak == "여름":
                if year == MISSED_PREORDER_YEAR and product["PRODUCT_ID"] == STOCKOUT_PRODUCT:
                    continue
                pre = date(year, 3, 5)
            else:
                pre = date(year, 9, 5)
            if not (period_first <= pre <= last_day):
                continue

            expected = pre + timedelta(days=int(supplier["LEAD_TIME_DAYS"]))
            rows.append({
                "ORDER_ID": "",
                "PRODUCT_ID": product["PRODUCT_ID"],
                "SUPPLIER_ID": supplier["SUPPLIER_ID"],
                "ORDER_DATE": pre.isoformat(),
                "EXPECTED_DATE": expected.isoformat(),
                "QTY": max(int(supplier["MOQ"]), 1500),
                "UNIT_COST": int(round(int(product["PRICE_KRW"]) * 0.4 / 100) * 100),
                "STATUS": "DELIVERED" if expected <= last_day else "IN_TRANSIT",
            })

    rows.sort(key=lambda r: (r["ORDER_DATE"], r["PRODUCT_ID"]))
    for i, row in enumerate(rows, start=1):
        row["ORDER_ID"] = f"ORD{i:05d}"
    return rows


# ── 반품 ────────────────────────────────────────────────────────────────
def build_returns(masters: Masters, sales: List[dict], rng: random.Random) -> List[dict]:
    """월 반품 수량을 개별 반품 건으로 분해합니다."""
    rows: List[dict] = []
    products = masters.product_by_id

    for sale in sales:
        # 면세점 반품은 별도 프로세스로 관리되어 이 테이블에 집계되지 않는다.
        if sale["RETURN_QTY"] < 3 or sale["CHANNEL_ID"] == "CH005":
            continue

        pid = sale["PRODUCT_ID"]
        year, month = (int(x) for x in sale["YEAR_MONTH"].split("-"))
        quality_spike = (pid == QUALITY_ISSUE_PRODUCT
                         and month_index((year, month)) >= month_index(QUALITY_ISSUE_FROM))
        reasons = ([("품질불량", 0.72), ("단순변심", 0.16), ("배송파손", 0.08), ("기타", 0.04)]
                   if quality_spike else RETURN_REASONS)

        remaining = sale["RETURN_QTY"]
        events = min(3, max(1, remaining // 6))
        for e in range(events):
            qty = remaining if e == events - 1 else max(1, remaining // (events - e))
            remaining -= qty
            if qty <= 0:
                continue
            rows.append({
                "RETURN_ID": "",
                "PRODUCT_ID": pid,
                "CHANNEL_ID": sale["CHANNEL_ID"],
                "RETURN_DATE": date(year, month, rng.randint(1, month_end((year, month)).day)).isoformat(),
                "QTY": qty,
                "REASON": weighted_choice(rng, reasons),
                "REFUND_AMOUNT": qty * int(products[pid]["PRICE_KRW"]),
            })

    rows.sort(key=lambda r: (r["RETURN_DATE"], r["PRODUCT_ID"]))
    for i, row in enumerate(rows, start=1):
        row["RETURN_ID"] = f"RET{i:05d}"
    return rows


# ── CS / 품질 클레임 처리 실적 ──────────────────────────────────────────
CS_ISSUE_TYPES = [
    ("품질불량", 0.30),
    ("배송지연", 0.22),
    ("파손", 0.18),
    ("사용법문의", 0.16),
    ("교환요청", 0.14),
]
CS_SEVERITY = [("HIGH", 0.18), ("MEDIUM", 0.42), ("LOW", 0.40)]
CS_HANDLING_DAYS = {"HIGH": (5, 12), "MEDIUM": (2, 6), "LOW": (1, 3)}


def build_cs_tickets(masters: Masters, returns: List[dict], rng: random.Random) -> List[dict]:
    """반품 건에 연동된 CS 접수·처리 실적을 만듭니다.

    품질불량 반품은 대부분 CS 티켓을 남기고, 나머지는 일부만 접수됩니다.
    처리소요일은 심각도에 따라 달라지며 HIGH 는 보상금이 발생합니다.
    """
    rows: List[dict] = []
    products = masters.product_by_id
    last_day = month_end(month_sequence(PERIOD_START, PERIOD_MONTHS)[-1])

    for ret in returns:
        is_quality = ret["REASON"] == "품질불량"
        if not is_quality and rng.random() > 0.35:
            continue

        received = date.fromisoformat(ret["RETURN_DATE"]) + timedelta(days=rng.randint(0, 3))
        if received > last_day:
            continue

        issue = "품질불량" if is_quality else weighted_choice(rng, CS_ISSUE_TYPES)
        severity = ("HIGH" if is_quality and rng.random() < 0.45
                    else weighted_choice(rng, CS_SEVERITY))
        handling = rng.randint(*CS_HANDLING_DAYS[severity])
        resolved: Optional[date] = received + timedelta(days=handling)

        if resolved and resolved <= last_day:
            status = "RESOLVED"
        else:
            status, resolved = "IN_PROGRESS", None

        compensation = 0
        if severity == "HIGH" and status == "RESOLVED":
            unit = int(products[ret["PRODUCT_ID"]]["PRICE_KRW"])
            compensation = int(round(unit * ret["QTY"] * rng.uniform(0.3, 1.0) / 1000) * 1000)

        rows.append({
            "TICKET_ID": "",
            "PRODUCT_ID": ret["PRODUCT_ID"],
            "CHANNEL_ID": ret["CHANNEL_ID"],
            "RECEIVED_DATE": received.isoformat(),
            "ISSUE_TYPE": issue,
            "SEVERITY": severity,
            "STATUS": status,
            "RESOLVED_DATE": resolved.isoformat() if resolved else "",
            "HANDLING_DAYS": handling if status == "RESOLVED" else "",
            "COMPENSATION_AMOUNT": compensation,
        })

    rows.sort(key=lambda r: (r["RECEIVED_DATE"], r["PRODUCT_ID"]))
    for i, row in enumerate(rows, start=1):
        row["TICKET_ID"] = f"CS{i:05d}"
    return rows


# ── 프로모션 실적 ───────────────────────────────────────────────────────
def build_promotion_results(masters: Masters, sales: List[dict],
                            promo_hits: Dict[Tuple[str, str, Tuple[int, int]], List[str]]
                            ) -> List[dict]:
    """이벤트별 제품 실적 — 프로모션 기간에 걸린 판매를 프로모션에 귀속시킵니다.

    UPLIFT_PCT 는 "프로모션이 없던 달의 평균 판매량" 대비 상승률입니다.
    """
    promos = {p["PROMOTION_ID"]: p for p in masters.promotions}
    sale_index = {(s["PRODUCT_ID"], s["CHANNEL_ID"], s["YEAR_MONTH"]): s for s in sales}

    baseline: Dict[Tuple[str, str], List[int]] = {}
    for sale in sales:
        year, month = (int(x) for x in sale["YEAR_MONTH"].split("-"))
        if (sale["PRODUCT_ID"], sale["CHANNEL_ID"], (year, month)) in promo_hits:
            continue
        baseline.setdefault((sale["PRODUCT_ID"], sale["CHANNEL_ID"]), []).append(sale["SALES_QTY"])

    rows: List[dict] = []
    for (pid, cid, ym), promo_ids in sorted(promo_hits.items(),
                                            key=lambda kv: (kv[0][2], kv[0][0], kv[0][1])):
        sale = sale_index.get((pid, cid, month_key(ym)))
        if sale is None:
            continue

        base_vals = baseline.get((pid, cid), [])
        base_qty = sum(base_vals) / len(base_vals) if base_vals else sale["SALES_QTY"]
        uplift = (sale["SALES_QTY"] / base_qty - 1) * 100 if base_qty else 0.0

        for promo_id in promo_ids:
            rows.append({
                "RESULT_ID": "",
                "PROMOTION_ID": promo_id,
                "PRODUCT_ID": pid,
                "CHANNEL_ID": cid,
                "YEAR_MONTH": month_key(ym),
                "SALES_QTY": sale["SALES_QTY"],
                "SALES_AMOUNT": sale["SALES_AMOUNT"],
                "DISCOUNT_AMOUNT": int(round(sale["SALES_AMOUNT"]
                                             * float(promos[promo_id]["DISCOUNT_RATE"]))),
                "UPLIFT_PCT": round(uplift, 1),
            })

    for i, row in enumerate(rows, start=1):
        row["RESULT_ID"] = f"PRS{i:05d}"
    return rows


# ── 검증 ────────────────────────────────────────────────────────────────
class ValidationReport:
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.checks: List[str] = []

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append(f"{'OK ' if ok else 'X  '}{name}{('  ' + detail) if detail else ''}")
        if not ok:
            self.errors.append(f"{name} {detail}".strip())

    def fk(self, name: str, values: Iterable, allowed: Iterable) -> None:
        orphans = sorted(set(values) - set(allowed))
        self.check(name, not orphans, f"고아값={orphans[:5]}" if orphans else "")

    def render(self) -> str:
        lines = ["", "=== 검증 결과 ==="] + [f"  {c}" for c in self.checks]
        lines += ["", f"  실패 {len(self.errors)}건 / 전체 {len(self.checks)}건"]
        return "\n".join(lines)


def validate(masters: Masters, sales: List[dict], inventory: List[dict], orders: List[dict],
             returns: List[dict], tickets: List[dict], promo_results: List[dict]
             ) -> ValidationReport:
    r = ValidationReport()
    pids = {p["PRODUCT_ID"] for p in masters.products}
    cids = {c["CHANNEL_ID"] for c in masters.channels}
    sids = {s["SUPPLIER_ID"] for s in masters.suppliers}
    wids = {w["WAREHOUSE_ID"] for w in masters.warehouses}
    prids = {p["PROMOTION_ID"] for p in masters.promotions}

    # 참조 무결성 — 과거 결함이 재발하면 여기서 잡힌다.
    r.fk("MST_PRODUCT.SUPPLIER_ID -> MST_SUPPLIER", (p["SUPPLIER_ID"] for p in masters.products), sids)
    r.fk("MST_PROMOTION.CHANNEL_ID -> MST_CHANNEL", (p["CHANNEL_ID"] for p in masters.promotions), cids)
    r.fk("FACT_MONTHLY_SALES.PRODUCT_ID", (s["PRODUCT_ID"] for s in sales), pids)
    r.fk("FACT_MONTHLY_SALES.CHANNEL_ID", (s["CHANNEL_ID"] for s in sales), cids)
    r.fk("FACT_INVENTORY.PRODUCT_ID", (i["PRODUCT_ID"] for i in inventory), pids)
    r.fk("FACT_INVENTORY.WAREHOUSE_ID", (i["WAREHOUSE_ID"] for i in inventory), wids)
    r.fk("FACT_ORDER.PRODUCT_ID", (o["PRODUCT_ID"] for o in orders), pids)
    r.fk("FACT_ORDER.SUPPLIER_ID", (o["SUPPLIER_ID"] for o in orders), sids)
    r.fk("FACT_RETURN.PRODUCT_ID", (x["PRODUCT_ID"] for x in returns), pids)
    r.fk("FACT_RETURN.CHANNEL_ID", (x["CHANNEL_ID"] for x in returns), cids)
    r.fk("FACT_CS_TICKET.PRODUCT_ID", (t["PRODUCT_ID"] for t in tickets), pids)
    r.fk("FACT_CS_TICKET.CHANNEL_ID", (t["CHANNEL_ID"] for t in tickets), cids)
    r.fk("FACT_PROMOTION_RESULT.PROMOTION_ID", (p["PROMOTION_ID"] for p in promo_results), prids)
    r.fk("FACT_PROMOTION_RESULT.PRODUCT_ID", (p["PRODUCT_ID"] for p in promo_results), pids)

    # 커버리지 — 과거 결함: 제품 20개 중 판매 실적이 1개뿐이었다.
    sold = {s["PRODUCT_ID"] for s in sales}
    r.check("모든 제품에 판매 실적 존재", sold == pids, f"누락={sorted(pids - sold)}")

    # LOGIC_DOCUMENT 규칙과의 일치
    bad_status = [i["INVENTORY_ID"] for i in inventory
                  if i["STOCK_STATUS"] != stock_status(i["STOCK_QTY"], i["SAFETY_STOCK_QTY"])]
    r.check("재고 상태가 문서 임계값과 일치", not bad_status, f"불일치={len(bad_status)}건")

    bad_net = [s["SALE_ID"] for s in sales
               if s["NET_SALES_QTY"] != s["SALES_QTY"] - s["RETURN_QTY"]]
    r.check("NET_SALES_QTY = SALES_QTY - RETURN_QTY", not bad_net, f"불일치={len(bad_net)}건")

    early = [s["SALE_ID"] for s in sales
             if month_index(tuple(int(x) for x in s["YEAR_MONTH"].split("-")))
             < (lambda d: d.year * 12 + d.month)(
                 date.fromisoformat(masters.product_by_id[s["PRODUCT_ID"]]["LAUNCH_DATE"]))]
    r.check("출시일 이전 판매 없음", not early, f"위반={len(early)}건")

    after_disc = [s["SALE_ID"] for s in sales
                  if s["PRODUCT_ID"] in DISCONTINUE_LAST_SALE
                  and month_index(tuple(int(x) for x in s["YEAR_MONTH"].split("-")))
                  > month_index(DISCONTINUE_LAST_SALE[s["PRODUCT_ID"]])]
    r.check("단종 이후 판매 없음", not after_disc, f"위반={len(after_disc)}건")

    bad_lead = [o["ORDER_ID"] for o in orders
                if (date.fromisoformat(o["EXPECTED_DATE"])
                    - date.fromisoformat(o["ORDER_DATE"])).days
                < int(masters.supplier_by_id[o["SUPPLIER_ID"]]["LEAD_TIME_DAYS"])]
    r.check("발주 리드타임 >= 공급사 기준", not bad_lead, f"위반={len(bad_lead)}건")

    resolved_bad = [t["TICKET_ID"] for t in tickets
                    if t["STATUS"] == "RESOLVED" and not t["RESOLVED_DATE"]]
    r.check("처리완료 티켓에 처리일 존재", not resolved_bad, f"위반={len(resolved_bad)}건")

    # 심어둔 시나리오가 실제로 데이터에 나타나는지
    critical = [i for i in inventory
                if i["PRODUCT_ID"] == STOCKOUT_PRODUCT and i["STOCK_STATUS"] == "CRITICAL"]
    r.check(f"결품 시나리오({STOCKOUT_PRODUCT}) CRITICAL 존재", bool(critical), f"{len(critical)}건")

    dead = [i for i in inventory if i["STOCK_STATUS"] == "DEADSTOCK"]
    r.check("단종 악성재고(DEADSTOCK) 존재", bool(dead), f"{len(dead)}건")

    quality = [t for t in tickets
               if t["PRODUCT_ID"] == QUALITY_ISSUE_PRODUCT and t["ISSUE_TYPE"] == "품질불량"]
    r.check(f"품질 이슈 시나리오({QUALITY_ISSUE_PRODUCT}) CS 존재", bool(quality), f"{len(quality)}건")

    delayed = [o for o in orders if o["STATUS"] == "DELAYED"]
    r.check("해외 공급사 발주 지연 존재", bool(delayed), f"{len(delayed)}건")

    promoted = {p["PROMOTION_ID"] for p in promo_results}
    r.check("모든 프로모션에 실적 존재", promoted == prids, f"누락={sorted(prids - promoted)}")

    return r


# ── 진입점 ──────────────────────────────────────────────────────────────
OUTPUT_COLUMNS: Dict[str, List[str]] = {
    "FACT_MONTHLY_SALES": ["SALE_ID", "PRODUCT_ID", "CHANNEL_ID", "YEAR_MONTH", "SALES_QTY",
                           "SALES_AMOUNT", "CURRENCY", "RETURN_QTY", "NET_SALES_QTY"],
    "FACT_INVENTORY": ["INVENTORY_ID", "PRODUCT_ID", "WAREHOUSE_ID", "SNAPSHOT_DATE", "STOCK_QTY",
                       "SAFETY_STOCK_QTY", "REORDER_POINT", "COVERAGE_WEEKS", "STOCK_STATUS"],
    "FACT_ORDER": ["ORDER_ID", "PRODUCT_ID", "SUPPLIER_ID", "ORDER_DATE", "EXPECTED_DATE",
                   "QTY", "UNIT_COST", "STATUS"],
    "FACT_RETURN": ["RETURN_ID", "PRODUCT_ID", "CHANNEL_ID", "RETURN_DATE", "QTY", "REASON",
                    "REFUND_AMOUNT"],
    "FACT_CS_TICKET": ["TICKET_ID", "PRODUCT_ID", "CHANNEL_ID", "RECEIVED_DATE", "ISSUE_TYPE",
                       "SEVERITY", "STATUS", "RESOLVED_DATE", "HANDLING_DAYS",
                       "COMPENSATION_AMOUNT"],
    "FACT_PROMOTION_RESULT": ["RESULT_ID", "PROMOTION_ID", "PRODUCT_ID", "CHANNEL_ID",
                              "YEAR_MONTH", "SALES_QTY", "SALES_AMOUNT", "DISCOUNT_AMOUNT",
                              "UPLIFT_PCT"],
}


def generate(base: Path) -> Dict[str, List[dict]]:
    rng = random.Random(SEED)
    masters = load_masters(base)
    months = month_sequence(PERIOD_START, PERIOD_MONTHS)

    sales, monthly_total, promo_hits = build_sales(masters, months, rng)
    inventory = build_inventory(masters, months, monthly_total, rng)
    orders = build_orders(masters, inventory, rng)
    returns = build_returns(masters, sales, rng)
    tickets = build_cs_tickets(masters, returns, rng)
    promo_results = build_promotion_results(masters, sales, promo_hits)

    report = validate(masters, sales, inventory, orders, returns, tickets, promo_results)
    print(report.render())
    if report.errors:
        raise SystemExit("검증 실패 — 파일을 쓰지 않고 중단합니다.")

    return {
        "FACT_MONTHLY_SALES": sales,
        "FACT_INVENTORY": inventory,
        "FACT_ORDER": orders,
        "FACT_RETURN": returns,
        "FACT_CS_TICKET": tickets,
        "FACT_PROMOTION_RESULT": promo_results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="뷰티 이커머스 데모 데이터 생성")
    parser.add_argument("--out", type=Path, default=DEFAULT_DIR, help="출력 디렉터리")
    parser.add_argument("--src", type=Path, default=DEFAULT_DIR, help="마스터 CSV 디렉터리")
    parser.add_argument("--dry-run", action="store_true", help="파일을 쓰지 않고 검증만")
    args = parser.parse_args()

    tables = generate(args.src)

    print()
    print("=== 생성 결과 ===")
    for name, rows in tables.items():
        print(f"  {name:24} {len(rows):5}행")

    if args.dry_run:
        print("\n--dry-run: 파일을 쓰지 않았습니다.")
        return

    args.out.mkdir(parents=True, exist_ok=True)
    for name, rows in tables.items():
        write_csv(args.out / f"{name}.csv", rows, OUTPUT_COLUMNS[name])
    print(f"\n{args.out} 에 {len(tables)}개 파일을 저장했습니다.")


if __name__ == "__main__":
    main()
