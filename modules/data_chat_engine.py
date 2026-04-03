"""
[역할] CSV 데이터 기반 채팅 답변 엔진

질문 유형 분류 → pandas 분석 → 구조화 답변(DataAnswer) 반환

질문 유형:
  CHART      : 그래프·차트·추이 요청
  RANKING    : TOP-N·순위·잘팔리는 요청
  COMPARISON : 비교·대비·YoY 요청
  RISK       : 위험·결품·발주 필요 요청
  DESCRIPTION: 설명·특징·문서 결합 요청

DataAnswer:
  summary        — 한 줄 요약
  interpretation — 전체 해석 (Claude)
  metrics        — 핵심 수치 3개 [{"label","value","delta"}]
  charts         — plotly figures
  datasets       — 사용 CSV 파일명 목록
  documents      — RAG 추천 문서 (DESCRIPTION 시)
  question_type  — 위 유형 중 하나
"""
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from modules.data_analyst import load_csv

# ── 질문 유형 상수 ─────────────────────────────────────────────────────────────
CHART       = "chart"
RANKING     = "ranking"
COMPARISON  = "comparison"
RISK        = "risk"
DESCRIPTION = "description"

_PROD_RE   = re.compile(r"(FG-\d+|PRD\d+)", re.IGNORECASE)
_METER_RE  = re.compile(r"\b(MTR\d+)\b", re.IGNORECASE)
_SEASON    = {"여름": [6,7,8], "봄": [3,4,5], "가을": [9,10,11], "겨울": [12,1,2]}

_ENERGY_KW = ["usage_kwh", "is_peak_day", "peak_kw", "전력", "kwh", "에너지",
              "계량기", "산업단지", "전기소비", "전력소비", "피크데이"]

_CHART_KW   = ["그래프", "차트", "그려줘", "시각화", "플롯", "추이", "트렌드"]
_RANKING_KW = ["top", "상위", "잘팔리", "잘 팔리", "많이 팔", "순위", "베스트", "best",
               "랭킹", "높은", "여름에", "봄에", "가을에", "겨울에"]
_COMP_KW    = ["비교", "vs", "대비", "차이", "증감", "동기", "yoy", "mom", "전년", "작년"]
_RISK_KW    = ["위험", "위기", "부족", "결품", "품절", "critical", "stockout",
               "발주 필요", "발주필요", "주문 필요", "보충"]


# ══════════════════════════════════════════════════════════════════════════════
# 데이터 클래스
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class DataAnswer:
    question_type:  str
    summary:        str                      # 한 줄 요약
    interpretation: str                      # 전체 해석 (마크다운)
    metrics:        List[Dict[str, str]]     # [{"label","value","delta"}, ...]
    charts:         List[Any]                # plotly figures
    datasets:       List[str]                # CSV 파일명
    documents:      List[str] = field(default_factory=list)
    kg_nodes:       int       = 0


# ══════════════════════════════════════════════════════════════════════════════
# 질문 분류
# ══════════════════════════════════════════════════════════════════════════════

def classify_question(msg: str) -> str:
    m  = msg.lower()
    has_prod = bool(_PROD_RE.search(msg))

    # 제품 코드 + 차트 = CHART
    if has_prod:
        return CHART
    # 명시적 차트 키워드
    if any(k in m for k in _CHART_KW):
        # 위험 차트보다 RISK가 우선
        if any(k in m for k in _RISK_KW):
            return RISK
        return CHART
    if any(k in m for k in _RISK_KW):
        return RISK
    if any(k in m for k in _COMP_KW):
        return COMPARISON
    if any(k in m for k in _RANKING_KW):
        return RANKING
    return DESCRIPTION


# ══════════════════════════════════════════════════════════════════════════════
# 내부 헬퍼: 데이터 분석
# ══════════════════════════════════════════════════════════════════════════════

def _resolve_name(product_id: str, parts_df: Optional[pd.DataFrame]) -> str:
    if parts_df is None:
        return product_id
    row = parts_df[parts_df["LINKED_PRODUCT_ID"] == product_id]
    return row.iloc[0]["PART_NAME"] if not row.empty else product_id


def _detect_season(msg: str) -> Optional[str]:
    for s in _SEASON:
        if s in msg:
            return s
    return None


# ── ENERGY CHART ──────────────────────────────────────────────────────────────

def _build_chart_energy(meter_id: str, msg: str) -> Tuple[List[Any], str, List[str], List[Dict], str]:
    """MTR* 계량기의 월별 USAGE_KWH(막대) + IS_PEAK_DAY 일수(꺾은선) 복합 차트."""
    charts, datasets = [], []

    usage = load_csv("energy_fact_daily_usage.csv")
    meter = load_csv("energy_mst_meter.csv")

    if usage is None:
        return [], meter_id, [], [], "에너지 사용량 데이터 없음"
    datasets.append("energy_fact_daily_usage.csv")

    # 컬럼 대소문자 정규화
    usage.columns = [c.upper() for c in usage.columns]

    meter_name = meter_id
    if meter is not None:
        meter.columns = [c.upper() for c in meter.columns]
        datasets.append("energy_mst_meter.csv")
        row = meter[meter["METER_ID"].str.upper() == meter_id.upper()]
        if not row.empty:
            meter_name = row.iloc[0].get("METER_NAME", meter_id)

    # 해당 계량기 필터
    df = usage[usage["METER_ID"].str.upper() == meter_id.upper()].copy()
    if df.empty:
        return [], meter_name, datasets, [], f"{meter_name} 데이터 없음"

    # USAGE_DATE → YEAR_MONTH 추출
    df["YEAR_MONTH"] = pd.to_datetime(df["USAGE_DATE"]).dt.to_period("M").astype(str)
    monthly = df.groupby("YEAR_MONTH").agg(
        USAGE_KWH=("USAGE_KWH", "sum"),
        PEAK_DAYS=("IS_PEAK_DAY", "sum"),
    ).reset_index().sort_values("YEAR_MONTH")

    # 이중 축 복합 차트
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly["YEAR_MONTH"], y=monthly["USAGE_KWH"],
        name="전력 소비(kWh)", marker_color="#2563EB", yaxis="y1",
    ))
    fig.add_trace(go.Scatter(
        x=monthly["YEAR_MONTH"], y=monthly["PEAK_DAYS"],
        name="피크데이(일수)", mode="lines+markers",
        line=dict(color="#F59E0B", width=2), yaxis="y2",
    ))
    fig.update_layout(
        title=f"{meter_name} 월별 전력 소비 & 피크데이",
        yaxis=dict(title="USAGE_KWH (kWh)"),
        yaxis2=dict(title="IS_PEAK_DAY (일)", overlaying="y", side="right"),
        legend=dict(x=0, y=1.1, orientation="h"),
        height=380, margin=dict(t=60, b=40),
    )
    charts.append(fig)

    total_kwh   = int(monthly["USAGE_KWH"].sum())
    avg_kwh     = int(monthly["USAGE_KWH"].mean())
    peak_m      = monthly.loc[monthly["USAGE_KWH"].idxmax()]
    metrics = [
        {"label": "총 소비량", "value": f"{total_kwh:,} kWh", "delta": ""},
        {"label": "월 평균",   "value": f"{avg_kwh:,} kWh",   "delta": ""},
        {"label": "최대 소비월","value": str(peak_m["YEAR_MONTH"]),
         "delta": f"{int(peak_m['USAGE_KWH']):,} kWh"},
    ]
    data_sum = (
        f"[{meter_name} 월별 전력 소비 요약]\n"
        f"총 소비량: {total_kwh:,} kWh / 월 평균: {avg_kwh:,} kWh / "
        f"최대 소비월: {peak_m['YEAR_MONTH']} ({int(peak_m['USAGE_KWH']):,} kWh)\n"
        f"월별 피크데이 합계: {int(monthly['PEAK_DAYS'].sum())}일\n"
        + "\n".join(
            f"  {r['YEAR_MONTH']}: {int(r['USAGE_KWH']):,} kWh, 피크 {int(r['PEAK_DAYS'])}일"
            for _, r in monthly.iterrows()
        )
    )
    return charts, meter_name, datasets, metrics, data_sum


# ── CHART ─────────────────────────────────────────────────────────────────────

def _build_chart_product(code: str) -> Tuple[List[Any], str, List[str], List[Dict], str]:
    """Returns (charts, product_name, datasets, metrics, data_summary)"""
    charts, datasets = [], []
    sales = load_csv("FACT_MONTHLY_SALES.csv")
    parts = load_csv("MST_PART.csv")
    if sales is None:
        return [], code, [], [], "판매 데이터 없음"
    datasets.append("FACT_MONTHLY_SALES.csv")
    if parts is not None:
        datasets.append("MST_PART.csv")

    code_u = code.upper()
    product_id, product_name = code_u, code_u
    if code_u.startswith("FG-") and parts is not None:
        row = parts[parts["PART_CD"] == code_u]
        if not row.empty:
            product_id   = row.iloc[0]["LINKED_PRODUCT_ID"]
            product_name = row.iloc[0]["PART_NAME"]
    else:
        product_name = _resolve_name(code_u, parts)

    df = sales[sales["PRODUCT_ID"] == product_id].sort_values("YEAR_MONTH").copy()
    if df.empty:
        return [], product_name, datasets, [], f"{product_name} 판매 데이터 없음"

    fig = px.line(df, x="YEAR_MONTH", y="NET_SALES_QTY",
                  title=f"{product_name} 월별 수요 추이",
                  labels={"YEAR_MONTH": "월", "NET_SALES_QTY": "판매량"},
                  markers=True)
    fig.update_layout(height=300, margin=dict(t=40, b=30))
    charts.append(fig)

    total = int(df["NET_SALES_QTY"].sum())
    avg   = int(df["NET_SALES_QTY"].mean())
    peak_row = df.loc[df["NET_SALES_QTY"].idxmax()]
    metrics = [
        {"label": "총 판매량", "value": f"{total:,}개", "delta": ""},
        {"label": "월 평균", "value": f"{avg:,}개", "delta": ""},
        {"label": "최고 판매월", "value": str(peak_row["YEAR_MONTH"]),
         "delta": f"{int(peak_row['NET_SALES_QTY']):,}개"},
    ]
    data_summary = (
        f"[{product_name} 판매 요약]\n"
        f"총 판매량: {total:,}개 / 월 평균: {avg:,}개 / "
        f"최고 판매월: {peak_row['YEAR_MONTH']} ({int(peak_row['NET_SALES_QTY']):,}개)"
    )
    return charts, product_name, datasets, metrics, data_summary


def _build_chart_channel(recent_months: int = 0) -> Tuple[List[Any], List[str], List[Dict], str]:
    charts, datasets = [], []
    sales = load_csv("FACT_MONTHLY_SALES.csv")
    ch_df = load_csv("MST_CHANNEL.csv")
    if sales is None or ch_df is None:
        return [], [], [], "채널 판매 데이터 없음"
    datasets.extend(["FACT_MONTHLY_SALES.csv", "MST_CHANNEL.csv"])

    merged = sales.merge(ch_df[["CHANNEL_ID", "CHANNEL_NAME"]], on="CHANNEL_ID", how="left")
    if recent_months > 0:
        months = sorted(merged["YEAR_MONTH"].unique())[-recent_months:]
        merged = merged[merged["YEAR_MONTH"].isin(months)]

    grouped = merged.groupby(["YEAR_MONTH", "CHANNEL_NAME"])["NET_SALES_QTY"].sum().reset_index()
    fig = px.line(grouped, x="YEAR_MONTH", y="NET_SALES_QTY", color="CHANNEL_NAME",
                  title="채널별 월별 판매 추이",
                  labels={"YEAR_MONTH": "월", "NET_SALES_QTY": "판매량"},
                  markers=True)
    fig.update_layout(height=300, margin=dict(t=40, b=30))
    charts.append(fig)

    ch_total = grouped.groupby("CHANNEL_NAME")["NET_SALES_QTY"].sum()
    top_ch   = ch_total.idxmax()
    metrics  = [
        {"label": "채널 수", "value": f"{len(ch_total)}개", "delta": ""},
        {"label": "1위 채널", "value": top_ch, "delta": ""},
        {"label": "1위 판매량", "value": f"{int(ch_total[top_ch]):,}개", "delta": ""},
    ]
    data_summary = (
        "[채널별 판매 요약]\n"
        + "\n".join(f"  · {ch}: {int(v):,}개" for ch, v in ch_total.nlargest(5).items())
    )
    return charts, datasets, metrics, data_summary


# ── RANKING ───────────────────────────────────────────────────────────────────

def _build_ranking(msg: str) -> Tuple[List[Any], List[str], List[Dict], str]:
    charts, datasets = [], []
    m      = msg.lower()
    season = _detect_season(m)
    top_n  = 5

    sales = load_csv("FACT_MONTHLY_SALES.csv")
    parts = load_csv("MST_PART.csv")
    ch_df = load_csv("MST_CHANNEL.csv")
    if sales is None:
        return [], [], [], "판매 데이터 없음"
    datasets.append("FACT_MONTHLY_SALES.csv")
    if parts is not None:
        datasets.append("MST_PART.csv")

    # 채널별 TOP3 요청
    if "채널" in m and ch_df is not None:
        datasets.append("MST_CHANNEL.csv")
        merged = sales.merge(ch_df[["CHANNEL_ID", "CHANNEL_NAME"]], on="CHANNEL_ID", how="left")
        if parts is not None:
            merged = merged.merge(
                parts[["LINKED_PRODUCT_ID", "PART_NAME"]],
                left_on="PRODUCT_ID", right_on="LINKED_PRODUCT_ID", how="left"
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
        fig = px.bar(top3, x="CHANNEL_NAME", y="NET_SALES_QTY", color="label",
                     title="채널별 TOP3 판매 상품",
                     labels={"CHANNEL_NAME": "채널", "NET_SALES_QTY": "판매량", "label": "상품"})
        fig.update_layout(height=300, margin=dict(t=40, b=30))
        charts.append(fig)

        ch_total = top3.groupby("CHANNEL_NAME")["NET_SALES_QTY"].sum()
        metrics = [
            {"label": "분석 채널 수", "value": f"{len(ch_total)}개", "delta": ""},
            {"label": "최고 채널", "value": ch_total.idxmax(), "delta": ""},
            {"label": "최고 채널 매출", "value": f"{int(ch_total.max()):,}개", "delta": ""},
        ]
        lines = ["[채널별 TOP3 판매 상품]"]
        for _, row in top3.iterrows():
            lines.append(f"  · {row['CHANNEL_NAME']} | {row['label']}: {int(row['NET_SALES_QTY']):,}개")
        return charts, datasets, metrics, "\n".join(lines)

    # 계절 또는 전체 TOP-N
    df = sales.copy()
    if season and season in _SEASON:
        df["_m"] = df["YEAR_MONTH"].str[-2:].astype(int)
        df = df[df["_m"].isin(_SEASON[season])]
        title = f"{season} 판매 TOP{top_n}"
    else:
        title = f"전체 판매 TOP{top_n}"

    top = df.groupby("PRODUCT_ID")["NET_SALES_QTY"].sum().nlargest(top_n).reset_index()
    if parts is not None:
        top = top.merge(
            parts[["LINKED_PRODUCT_ID", "PART_NAME"]],
            left_on="PRODUCT_ID", right_on="LINKED_PRODUCT_ID", how="left"
        )
        top["label"] = top["PART_NAME"].fillna(top["PRODUCT_ID"])
    else:
        top["label"] = top["PRODUCT_ID"]

    fig = px.bar(top, x="NET_SALES_QTY", y="label", orientation="h",
                 title=title,
                 labels={"NET_SALES_QTY": "판매량", "label": "상품"},
                 color="NET_SALES_QTY",
                 color_continuous_scale="Blues")
    fig.update_layout(height=300, margin=dict(t=40, b=30), yaxis={"autorange": "reversed"})
    charts.append(fig)

    total_sales = int(top["NET_SALES_QTY"].sum())
    top1        = top.iloc[0]
    top1_share  = round(top1["NET_SALES_QTY"] / max(df["NET_SALES_QTY"].sum(), 1) * 100, 1)
    metrics = [
        {"label": "1위 상품", "value": top1["label"], "delta": ""},
        {"label": "1위 판매량", "value": f"{int(top1['NET_SALES_QTY']):,}개", "delta": ""},
        {"label": "TOP1 점유율", "value": f"{top1_share}%", "delta": ""},
    ]
    lines = [f"[{title}]"]
    for i, row in top.iterrows():
        lines.append(f"  {i+1}. {row['label']}: {int(row['NET_SALES_QTY']):,}개")
    return charts, datasets, metrics, "\n".join(lines)


# ── COMPARISON ────────────────────────────────────────────────────────────────

def _build_comparison(msg: str) -> Tuple[List[Any], List[str], List[Dict], str]:
    """YoY 또는 채널 비교"""
    charts, datasets = [], []
    sales = load_csv("FACT_MONTHLY_SALES.csv")
    parts = load_csv("MST_PART.csv")
    if sales is None:
        return [], [], [], "판매 데이터 없음"
    datasets.append("FACT_MONTHLY_SALES.csv")

    # YoY 비교
    sales["YEAR"] = sales["YEAR_MONTH"].str[:4]
    sales["MONTH"] = sales["YEAR_MONTH"].str[-2:].astype(int)
    yearly = sales.groupby("YEAR")["NET_SALES_QTY"].sum().reset_index()
    yearly["YEAR"] = yearly["YEAR"].astype(str)

    fig = px.bar(yearly, x="YEAR", y="NET_SALES_QTY",
                 title="연도별 총 판매량 비교",
                 labels={"YEAR": "연도", "NET_SALES_QTY": "판매량"},
                 color="NET_SALES_QTY", color_continuous_scale="Blues")
    fig.update_layout(height=300, margin=dict(t=40, b=30))
    charts.append(fig)

    years_sorted = yearly.sort_values("YEAR")
    if len(years_sorted) >= 2:
        prev = int(years_sorted.iloc[-2]["NET_SALES_QTY"])
        curr = int(years_sorted.iloc[-1]["NET_SALES_QTY"])
        yoy  = round((curr - prev) / max(prev, 1) * 100, 1)
        metrics = [
            {"label": "최근 연도", "value": f"{int(years_sorted.iloc[-1]['NET_SALES_QTY']):,}개",
             "delta": f"{'+' if yoy>0 else ''}{yoy}%"},
            {"label": "전년 대비", "value": f"{'+' if yoy>0 else ''}{yoy}%", "delta": ""},
            {"label": "분석 기간", "value": f"{len(yearly)}개 연도", "delta": ""},
        ]
    else:
        metrics = [{"label": "총 판매량", "value": f"{int(yearly['NET_SALES_QTY'].sum()):,}개", "delta": ""}]

    lines = ["[연도별 판매 비교]"]
    for _, row in years_sorted.iterrows():
        lines.append(f"  · {row['YEAR']}: {int(row['NET_SALES_QTY']):,}개")
    return charts, datasets, metrics, "\n".join(lines)


# ── RISK ─────────────────────────────────────────────────────────────────────

def _build_risk(msg: str) -> Tuple[List[Any], List[str], List[Dict], str]:
    charts, datasets = [], []
    m = msg.lower()

    inv   = load_csv("FACT_INVENTORY.csv")
    parts = load_csv("MST_PART.csv")
    orders = load_csv("FACT_REPLENISHMENT_ORDER.csv")

    lines = []
    metrics = []

    if inv is not None:
        datasets.append("FACT_INVENTORY.csv")
        if parts is not None:
            datasets.append("MST_PART.csv")

        latest   = inv.sort_values("SNAPSHOT_DATE").groupby("PRODUCT_ID").last().reset_index()
        critical = latest[latest["STOCK_STATUS"] == "CRITICAL"]
        warning  = latest[latest["STOCK_STATUS"] == "WARNING"]

        lines.append(f"[재고 위험 현황: CRITICAL {len(critical)}개 / WARNING {len(warning)}개]")
        for _, row in critical.iterrows():
            name = _resolve_name(row["PRODUCT_ID"], parts)
            lines.append(
                f"  · {name}: {row['STOCK_QTY']}개 "
                f"(안전재고 {row['SAFETY_STOCK_QTY']}개, 커버리지 {row.get('COVERAGE_WEEKS',0):.1f}주)"
            )

        # 커버리지 차트
        top_risk = latest.nsmallest(8, "COVERAGE_WEEKS").copy()
        if parts is not None:
            top_risk = top_risk.merge(
                parts[["LINKED_PRODUCT_ID", "PART_NAME"]],
                left_on="PRODUCT_ID", right_on="LINKED_PRODUCT_ID", how="left"
            )
        top_risk["label"] = top_risk.get("PART_NAME", top_risk["PRODUCT_ID"]).fillna(top_risk["PRODUCT_ID"])

        fig = px.bar(top_risk, x="label", y="COVERAGE_WEEKS",
                     color="STOCK_STATUS",
                     color_discrete_map={"CRITICAL":"#EF4444","WARNING":"#F59E0B","OK":"#10B981"},
                     title="재고 커버리지 (낮을수록 위험)",
                     labels={"label":"상품","COVERAGE_WEEKS":"재고 커버 주수"})
        fig.update_layout(height=280, margin=dict(t=40,b=30))
        charts.append(fig)

        metrics = [
            {"label": "🚨 CRITICAL", "value": f"{len(critical)}개", "delta": "즉시 조치 필요"},
            {"label": "⚠️ WARNING", "value": f"{len(warning)}개", "delta": ""},
            {"label": "최소 커버리지",
             "value": f"{top_risk['COVERAGE_WEEKS'].min():.1f}주" if not top_risk.empty else "-",
             "delta": ""},
        ]

    # 발주 필요 상품 (CRITICAL인데 발주 없음)
    if orders is not None and inv is not None and parts is not None:
        datasets.append("FACT_REPLENISHMENT_ORDER.csv")
        critical_pids = set(latest[latest["STOCK_STATUS"] == "CRITICAL"]["PRODUCT_ID"])
        active_parts  = set(orders[orders["STATUS"].isin(["PENDING","IN_TRANSIT"])]["PART_CD"])
        need_order = []
        for pid in critical_pids:
            pr = parts[parts["LINKED_PRODUCT_ID"] == pid]
            if pr.empty:
                continue
            pcd  = pr.iloc[0]["PART_CD"]
            name = pr.iloc[0]["PART_NAME"]
            if pcd not in active_parts:
                need_order.append(name)

        if need_order:
            lines.append(f"\n[즉시 발주 필요: {len(need_order)}개]")
            for n in need_order:
                lines.append(f"  · {n}")

            if not metrics:
                metrics = [{"label": "발주 필요", "value": f"{len(need_order)}개", "delta": "즉시 조치"}]

    if not lines:
        lines = ["재고/발주 데이터를 찾을 수 없습니다."]

    return charts, datasets, metrics, "\n".join(lines)


# ── DESCRIPTION (문서+데이터 결합) ────────────────────────────────────────────

def _build_description(
    msg: str, rag, kg
) -> Tuple[List[str], int, str]:
    """Returns (doc_files, kg_nodes, rag_context)"""
    doc_files: List[str] = []
    kg_nodes  = 0
    kg_ctx    = ""

    if kg:
        for word in msg.split()[:3]:
            result = kg.query_by_id(word)
            if result["matched_nodes"]:
                kg_nodes += len(result["matched_nodes"])
                nodes_str = ", ".join(
                    f"{n.get('label', n.get('id',''))}({n.get('type','')})" for n in result["matched_nodes"][:5]
                )
                kg_ctx = f"[지식그래프]\n{nodes_str}\n\n"
                break

    rag_ctx = ""
    if rag:
        hits = rag.query(msg, n_results=4)
        if hits:
            doc_files = list(dict.fromkeys(h["filename"] for h in hits))
            rag_ctx   = "\n\n".join(f"[{h['filename']}]\n{h['text']}" for h in hits)

    combined = kg_ctx + rag_ctx
    return doc_files, kg_nodes, combined


# ══════════════════════════════════════════════════════════════════════════════
# Claude 해석 생성
# ══════════════════════════════════════════════════════════════════════════════

def _claude_interpret(
    question: str,
    data_summary: str,
    metrics: List[Dict],
    question_type: str,
    domain_context: str,
    claude,
    doc_context: str = "",
) -> Tuple[str, str]:
    """
    Returns (summary_line, full_interpretation)
    Claude가 없으면 rule-based fallback.
    """
    if not claude:
        return _rule_summary(question_type, metrics), data_summary

    metrics_str = "\n".join(f"- {m['label']}: {m['value']}" for m in metrics[:3])
    doc_section = f"\n[관련 문서]\n{doc_context[:1500]}" if doc_context else ""

    prompt = (
        f"{domain_context}\n\n"
        f"[질문] {question}\n"
        f"[분석 유형] {question_type}\n"
        f"[핵심 수치]\n{metrics_str}\n"
        f"[데이터 요약]\n{data_summary[:2000]}"
        f"{doc_section}\n\n"
        "⚠️ 범위 표현은 반드시 `~` 하나만 사용 (예: 10~20개). `~~` 취소선 절대 금지.\n\n"
        "아래 형식으로 답변하세요:\n"
        "## 요약\n"
        "질문에 대한 한 줄 답변.\n\n"
        "## 해석\n"
        "데이터 기반으로 2~3문단 설명. 수치 언급, 비즈니스 시사점 포함.\n\n"
        "## 다음 할 일\n"
        "1. **[오늘]** — 구체적인 행동 + 이유 한 줄\n"
        "2. **[이번 주 내]** — 구체적인 행동 + 이유 한 줄\n"
        "3. **[이번 달 내]** — 구체적인 행동 + 이유 한 줄"
    )

    try:
        response = claude.generate(prompt, max_tokens=1100)
        sum_m    = re.search(r"##\s*요약\s*\n(.*?)(?=##|\Z)",   response, re.DOTALL)
        int_m    = re.search(r"##\s*해석\s*\n(.*?)(?=##|\Z)",   response, re.DOTALL)
        act_m    = re.search(r"##\s*다음 할 일\s*\n(.*?)(?=##|\Z)", response, re.DOTALL)
        summary  = sum_m.group(1).strip() if sum_m else response.split("\n")[0]
        interp   = int_m.group(1).strip() if int_m else response
        if act_m:
            interp += "\n\n---\n### 🗂️ 다음 할 일\n" + act_m.group(1).strip()
        return summary, interp
    except Exception:
        return _rule_summary(question_type, metrics), data_summary


def _rule_summary(question_type: str, metrics: List[Dict]) -> str:
    if not metrics:
        return "데이터를 분석했습니다."
    m0 = metrics[0]
    templates = {
        CHART:      f"{m0['label']}: {m0['value']}",
        RANKING:    f"1위: {m0['value']}",
        COMPARISON: f"전년 대비 {metrics[1]['value'] if len(metrics)>1 else ''}",
        RISK:       f"위험 상품 {m0['value']}",
        DESCRIPTION:"관련 데이터를 분석했습니다.",
    }
    return templates.get(question_type, "분석 완료")


# ══════════════════════════════════════════════════════════════════════════════
# 메인 진입점
# ══════════════════════════════════════════════════════════════════════════════

def analyze(
    msg: str,
    claude=None,
    rag=None,
    kg=None,
    domain_context: str = "",
) -> DataAnswer:
    """
    질문을 분류하고 분석 결과를 반환합니다.
    claude/rag/kg이 None이어도 rule 기반으로 동작합니다.
    """
    qtype = classify_question(msg)

    # ── ENERGY CHART (도메인 우선 감지) ───────────────────
    m_lower = msg.lower()
    is_energy = any(k in m_lower for k in _ENERGY_KW)
    meter_match = _METER_RE.search(msg)
    if (is_energy or meter_match) and any(k in m_lower for k in _CHART_KW):
        mid = meter_match.group(1) if meter_match else "MTR001"
        charts, name, datasets, metrics, data_sum = _build_chart_energy(mid, msg)
        summary, interp = _claude_interpret(msg, data_sum, metrics, CHART, domain_context, claude)
        return DataAnswer(CHART, summary, interp, metrics, charts, list(set(datasets)))

    # ── CHART ─────────────────────────────────────────────
    if qtype == CHART:
        match = _PROD_RE.search(msg)
        if match:
            charts, name, datasets, metrics, data_sum = _build_chart_product(match.group(1))
        else:
            recent = 3 if "최근" in msg else 0
            charts, datasets, metrics, data_sum = _build_chart_channel(recent)
        summary, interp = _claude_interpret(msg, data_sum, metrics, qtype, domain_context, claude)
        return DataAnswer(qtype, summary, interp, metrics, charts, list(set(datasets)))

    # ── RANKING ───────────────────────────────────────────
    if qtype == RANKING:
        charts, datasets, metrics, data_sum = _build_ranking(msg)
        summary, interp = _claude_interpret(msg, data_sum, metrics, qtype, domain_context, claude)
        return DataAnswer(qtype, summary, interp, metrics, charts, list(set(datasets)))

    # ── COMPARISON ────────────────────────────────────────
    if qtype == COMPARISON:
        charts, datasets, metrics, data_sum = _build_comparison(msg)
        summary, interp = _claude_interpret(msg, data_sum, metrics, qtype, domain_context, claude)
        return DataAnswer(qtype, summary, interp, metrics, charts, list(set(datasets)))

    # ── RISK ──────────────────────────────────────────────
    if qtype == RISK:
        charts, datasets, metrics, data_sum = _build_risk(msg)
        summary, interp = _claude_interpret(msg, data_sum, metrics, qtype, domain_context, claude)
        return DataAnswer(qtype, summary, interp, metrics, charts, list(set(datasets)))

    # ── DESCRIPTION: 데이터 + 문서 결합 ──────────────────
    doc_files, kg_nodes, doc_ctx = _build_description(msg, rag, kg)
    data_sum = ""

    # DESCRIPTION에서도 간단한 데이터 수집 시도
    sales = load_csv("FACT_MONTHLY_SALES.csv")
    parts = load_csv("MST_PART.csv")
    datasets: List[str] = []
    metrics = []

    prod_match = _PROD_RE.search(msg)
    if prod_match and sales is not None:
        charts_d, name_d, ds_d, metrics, sub_sum = _build_chart_product(prod_match.group(1))
        datasets.extend(ds_d)
        data_sum = sub_sum

    summary, interp = _claude_interpret(
        msg, data_sum, metrics, qtype, domain_context, claude, doc_ctx
    )
    return DataAnswer(
        qtype, summary, interp, metrics,
        charts=[], datasets=list(set(datasets)),
        documents=doc_files, kg_nodes=kg_nodes,
    )
