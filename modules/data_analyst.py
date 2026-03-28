"""
[역할] CSV/pandas 기반 데이터 분석 함수 모음
채팅 코파일럿·일일 브리핑에서 사용하는 순수 데이터 분석 함수입니다.
Streamlit에 의존하지 않으므로 독립적으로 테스트·재사용 가능합니다.

반환 규칙: 모든 함수는 (결과값, 사용된_파일_목록) 형태로 반환합니다.
"""
import os
import re
from typing import Any, List, Optional, Tuple

import pandas as pd
import plotly.express as px

DATA_DIR = "./data"


# ── 공통 로더 ─────────────────────────────────────────────────────────────────

def load_csv(filename: str) -> Optional[pd.DataFrame]:
    """data/ 폴더에서 CSV를 DataFrame으로 로드합니다."""
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        try:
            return pd.read_csv(path, encoding="utf-8-sig")
        except Exception:
            return None
    return None


def _resolve_product_name(product_id: str, parts_df: Optional[pd.DataFrame]) -> str:
    if parts_df is None:
        return product_id
    row = parts_df[parts_df["LINKED_PRODUCT_ID"] == product_id]
    return row.iloc[0]["PART_NAME"] if not row.empty else product_id


# ── 개별 상품 판매 차트 ───────────────────────────────────────────────────────

def product_sales_chart(
    product_code: str,
) -> Tuple[Optional[Any], str, List[str]]:
    """
    제품 코드(FG-XXX 또는 PRDXXX) → 월별 판매 line chart.
    Returns (fig | None, product_name, datasets_used)
    """
    datasets: List[str] = []
    sales_df = load_csv("FACT_MONTHLY_SALES.csv")
    parts_df = load_csv("MST_PART.csv")

    if sales_df is None:
        return None, product_code, datasets
    datasets.append("FACT_MONTHLY_SALES.csv")

    code = product_code.upper()
    product_id   = code
    product_name = code

    if code.startswith("FG-"):
        if parts_df is not None:
            datasets.append("MST_PART.csv")
            row = parts_df[parts_df["PART_CD"] == code]
            if row.empty:
                return None, code, datasets
            product_id   = row.iloc[0]["LINKED_PRODUCT_ID"]
            product_name = row.iloc[0]["PART_NAME"]
    else:
        if parts_df is not None:
            datasets.append("MST_PART.csv")
            product_name = _resolve_product_name(code, parts_df)

    filtered = sales_df[sales_df["PRODUCT_ID"] == product_id].sort_values("YEAR_MONTH")
    if filtered.empty:
        return None, product_name, datasets

    fig = px.line(
        filtered, x="YEAR_MONTH", y="NET_SALES_QTY",
        title=f"{product_name} 월별 수요",
        labels={"YEAR_MONTH": "월", "NET_SALES_QTY": "판매량"},
        markers=True,
    )
    fig.update_layout(height=280, margin=dict(t=40, b=30))
    return fig, product_name, datasets


# ── 채널별 판매 차트 ──────────────────────────────────────────────────────────

def channel_sales_chart(recent_months: int = 0) -> Tuple[Optional[Any], List[str]]:
    """채널별 월별 판매 line chart. Returns (fig | None, datasets_used)"""
    datasets: List[str] = []
    sales_df = load_csv("FACT_MONTHLY_SALES.csv")
    ch_df    = load_csv("MST_CHANNEL.csv")
    if sales_df is None or ch_df is None:
        return None, datasets
    datasets.extend(["FACT_MONTHLY_SALES.csv", "MST_CHANNEL.csv"])

    merged = sales_df.merge(ch_df[["CHANNEL_ID", "CHANNEL_NAME"]], on="CHANNEL_ID", how="left")
    if recent_months > 0:
        months = sorted(merged["YEAR_MONTH"].unique())[-recent_months:]
        merged = merged[merged["YEAR_MONTH"].isin(months)]

    grouped = (
        merged.groupby(["YEAR_MONTH", "CHANNEL_NAME"])["NET_SALES_QTY"]
        .sum().reset_index()
    )
    fig = px.line(
        grouped, x="YEAR_MONTH", y="NET_SALES_QTY", color="CHANNEL_NAME",
        title="채널별 월별 판매량",
        labels={"YEAR_MONTH": "월", "NET_SALES_QTY": "판매량"},
        markers=True,
    )
    fig.update_layout(height=280, margin=dict(t=40, b=30))
    return fig, datasets


# ── 계절·전체 판매 TOP-N ──────────────────────────────────────────────────────

_SEASON_MONTHS = {"여름": [6,7,8], "봄": [3,4,5], "가을": [9,10,11], "겨울": [12,1,2]}


def season_top_products(
    season: Optional[str] = None, top_n: int = 5
) -> Tuple[str, List[str]]:
    """계절별 또는 전체 판매 TOP-N 요약. Returns (summary_text, datasets_used)"""
    datasets: List[str] = []
    sales = load_csv("FACT_MONTHLY_SALES.csv")
    parts = load_csv("MST_PART.csv")
    if sales is None:
        return "판매 데이터 없음", []
    datasets.append("FACT_MONTHLY_SALES.csv")
    if parts is not None:
        datasets.append("MST_PART.csv")

    if season and season in _SEASON_MONTHS:
        df = sales.copy()
        df["_m"] = df["YEAR_MONTH"].str[-2:].astype(int)
        filtered = df[df["_m"].isin(_SEASON_MONTHS[season])]
        label = f"{season} 판매 TOP{top_n}"
    else:
        filtered = sales
        label = f"전체 판매 TOP{top_n}"

    top = filtered.groupby("PRODUCT_ID")["NET_SALES_QTY"].sum().nlargest(top_n)
    lines = [f"[{label}]"]
    for pid, qty in top.items():
        name = _resolve_product_name(pid, parts)
        lines.append(f"  · {name}: {qty:,}개")
    return "\n".join(lines), datasets


# ── 재고 위험 요약 ────────────────────────────────────────────────────────────

def inventory_risk_summary() -> Tuple[str, List[str]]:
    """재고 CRITICAL/WARNING 상품 요약. Returns (summary_text, datasets_used)"""
    datasets: List[str] = []
    inv   = load_csv("FACT_INVENTORY.csv")
    parts = load_csv("MST_PART.csv")
    if inv is None:
        return "재고 데이터 없음", []
    datasets.append("FACT_INVENTORY.csv")
    if parts is not None:
        datasets.append("MST_PART.csv")

    latest   = inv.sort_values("SNAPSHOT_DATE").groupby("PRODUCT_ID").last().reset_index()
    critical = latest[latest["STOCK_STATUS"] == "CRITICAL"]
    warning  = latest[latest["STOCK_STATUS"] == "WARNING"]

    lines = [f"[재고 위험 현황: CRITICAL {len(critical)}개 / WARNING {len(warning)}개]"]
    for _, row in critical.iterrows():
        name = _resolve_product_name(row["PRODUCT_ID"], parts)
        lines.append(f"  · {name}: {row['STOCK_QTY']}개 (안전재고 {row['SAFETY_STOCK_QTY']}개)")
    return "\n".join(lines), datasets


def inventory_coverage_chart() -> Tuple[Optional[Any], List[str]]:
    """재고 커버리지 bar chart (낮을수록 위험). Returns (fig | None, datasets_used)"""
    datasets: List[str] = []
    inv   = load_csv("FACT_INVENTORY.csv")
    parts = load_csv("MST_PART.csv")
    if inv is None:
        return None, []
    datasets.append("FACT_INVENTORY.csv")

    latest   = inv.sort_values("SNAPSHOT_DATE").groupby("PRODUCT_ID").last().reset_index()
    top_risk = latest.nsmallest(8, "COVERAGE_WEEKS").copy()

    if parts is not None:
        datasets.append("MST_PART.csv")
        top_risk = top_risk.merge(
            parts[["LINKED_PRODUCT_ID", "PART_NAME"]],
            left_on="PRODUCT_ID", right_on="LINKED_PRODUCT_ID", how="left",
        )
        top_risk["label"] = top_risk["PART_NAME"].fillna(top_risk["PRODUCT_ID"])
    else:
        top_risk["label"] = top_risk["PRODUCT_ID"]

    fig = px.bar(
        top_risk, x="label", y="COVERAGE_WEEKS",
        color="STOCK_STATUS",
        color_discrete_map={"CRITICAL": "#EF4444", "WARNING": "#F59E0B", "OK": "#10B981"},
        title="📦 재고 커버리지 (주 단위, 낮을수록 위험)",
        labels={"label": "상품", "COVERAGE_WEEKS": "재고 커버 주수"},
    )
    fig.update_layout(height=250, margin=dict(t=40, b=30))
    return fig, datasets


# ── 발주 관련 ─────────────────────────────────────────────────────────────────

def pending_orders_summary() -> Tuple[str, List[str]]:
    """진행중 발주 TOP5 요약. Returns (summary_text, datasets_used)"""
    datasets: List[str] = []
    orders = load_csv("FACT_REPLENISHMENT_ORDER.csv")
    parts  = load_csv("MST_PART.csv")
    if orders is None:
        return "발주 데이터 없음", []
    datasets.append("FACT_REPLENISHMENT_ORDER.csv")
    if parts is not None:
        datasets.append("MST_PART.csv")

    pending = orders[orders["STATUS"].isin(["PENDING", "IN_TRANSIT"])]
    lines = [f"[진행중 발주 {len(pending)}건]"]
    if parts is not None and not pending.empty:
        top5 = pending.groupby("PART_CD")["ORDER_QTY"].sum().nlargest(5)
        for part_cd, qty in top5.items():
            pr   = parts[parts["PART_CD"] == part_cd]
            name = pr.iloc[0]["PART_NAME"] if not pr.empty else part_cd
            lines.append(f"  · {name}: {qty:,}개 발주중")
    return "\n".join(lines), datasets


def replenishment_status() -> Tuple[str, List[str]]:
    """CRITICAL 재고 대비 발주 현황. Returns (summary_text, datasets_used)"""
    inv    = load_csv("FACT_INVENTORY.csv")
    orders = load_csv("FACT_REPLENISHMENT_ORDER.csv")
    parts  = load_csv("MST_PART.csv")
    if inv is None or orders is None or parts is None:
        return "데이터 없음", []
    datasets = ["FACT_INVENTORY.csv", "FACT_REPLENISHMENT_ORDER.csv", "MST_PART.csv"]

    latest        = inv.sort_values("SNAPSHOT_DATE").groupby("PRODUCT_ID").last().reset_index()
    critical_pids = set(latest[latest["STOCK_STATUS"] == "CRITICAL"]["PRODUCT_ID"])
    active_parts  = set(orders[orders["STATUS"].isin(["PENDING", "IN_TRANSIT"])]["PART_CD"])

    lines = ["[발주 필요 상품]"]
    for pid in critical_pids:
        pr = parts[parts["LINKED_PRODUCT_ID"] == pid]
        if pr.empty:
            continue
        pcd  = pr.iloc[0]["PART_CD"]
        name = pr.iloc[0]["PART_NAME"]
        status = "발주 진행중 ✓" if pcd in active_parts else "발주 없음 ⚠️"
        lines.append(f"  · {name}: {status}")
    return "\n".join(lines), datasets


# ── 채널 TOP3 차트 (브리핑용) ─────────────────────────────────────────────────

def channel_top3_chart() -> Tuple[Optional[Any], List[str]]:
    """채널별 TOP3 상품 bar chart (최근 3개월). Returns (fig | None, datasets_used)"""
    datasets: List[str] = []
    sales = load_csv("FACT_MONTHLY_SALES.csv")
    ch_df = load_csv("MST_CHANNEL.csv")
    parts = load_csv("MST_PART.csv")
    if sales is None or ch_df is None:
        return None, []
    datasets.extend(["FACT_MONTHLY_SALES.csv", "MST_CHANNEL.csv"])

    recent_months = sorted(sales["YEAR_MONTH"].unique())[-3:]
    recent = sales[sales["YEAR_MONTH"].isin(recent_months)]
    merged = recent.merge(ch_df[["CHANNEL_ID", "CHANNEL_NAME"]], on="CHANNEL_ID", how="left")

    if parts is not None:
        datasets.append("MST_PART.csv")
        merged = merged.merge(
            parts[["LINKED_PRODUCT_ID", "PART_NAME"]],
            left_on="PRODUCT_ID", right_on="LINKED_PRODUCT_ID", how="left",
        )
        merged["label"] = merged["PART_NAME"].fillna(merged["PRODUCT_ID"])
    else:
        merged["label"] = merged["PRODUCT_ID"]

    top3 = (
        merged.groupby(["CHANNEL_NAME", "label"])["NET_SALES_QTY"]
        .sum().reset_index()
        .sort_values("NET_SALES_QTY", ascending=False)
        .groupby("CHANNEL_NAME").head(3)
    )
    fig = px.bar(
        top3, x="CHANNEL_NAME", y="NET_SALES_QTY", color="label",
        title="📈 채널별 TOP3 상품 (최근 3개월)",
        labels={"CHANNEL_NAME": "채널", "NET_SALES_QTY": "판매량", "label": "상품"},
    )
    fig.update_layout(height=250, margin=dict(t=40, b=30))
    return fig, datasets
