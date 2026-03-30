"""
generate_energy.py
Power/gas utility operations demo data generator.
Outputs CSVs + SCHEMA_DEFINITION.json + LOGIC_DOCUMENT.txt
to <repo_root>/data/energy/
"""

import os
import csv
import json
import random
from datetime import date, datetime, timedelta

random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "energy")

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def write_csv(filename: str, fieldnames: list, rows: list) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows):,} rows -> {filepath}")


def nullable(value, null_prob: float = 0.20):
    """Return None with probability null_prob, else value."""
    return None if random.random() < null_prob else value


def fmt_date(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def date_range(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


# ---------------------------------------------------------------------------
# Master data constants
# ---------------------------------------------------------------------------

REGIONS = [
    ("RGN001", "수도권",   "광역시", 25.6, 12000, "수도권"),
    ("RGN002", "강원",     "도",      1.5,   800,  "북부"),
    ("RGN003", "충청",     "도",      5.6,  3500,  "남부"),
    ("RGN004", "전라",     "도",      5.2,  3200,  "남부"),
    ("RGN005", "경북",     "도",      2.6,  2100,  "북부"),
    ("RGN006", "경남",     "도",      3.4,  2800,  "남부"),
    ("RGN007", "부산경남", "광역시",  3.4,  3100,  "남부"),
    ("RGN008", "제주",     "도",      0.7,   400,  "남부"),
    ("RGN009", "울산경남", "광역시",  1.1,  2000,  "남부"),
]

# (PLANT_ID, PLANT_NAME, PLANT_TYPE, REGION_ID, CAPACITY_MW,
#  COMMISSION_DATE, STATUS, FUEL_TYPE, OPERATOR_NAME, CO2_EMISSION_FACTOR)
# CO2 = None for renewables (~30% of plants => explicit None)
PLANTS_RAW = [
    ("PLT001", "서울화력",     "화력",    "RGN001", 800,  "1990-03-15", "OPERATING",     "LNG",  "한국전력 수도권본부", 490),
    ("PLT002", "영동원자력",   "원자력",  "RGN002", 1400, "1998-07-20", "OPERATING",     "우라늄","한국수력원자력",     11),
    ("PLT003", "부산복합화력", "복합화력","RGN007", 600,  "2005-11-01", "OPERATING",     "LNG",  "한국중부발전",       370),
    ("PLT004", "전남태양광단지","태양광", "RGN004", 200,  "2018-04-10", "OPERATING",     "태양열","한국남부발전",       None),
    ("PLT005", "제주풍력",     "풍력",    "RGN008", 100,  "2016-09-05", "OPERATING",     "바람", "제주에너지공사",     None),
    ("PLT006", "충청화력",     "화력",    "RGN003", 1000, "1985-06-30", "OPERATING",     "석탄", "한국동서발전",       820),
    ("PLT007", "경북원자력",   "원자력",  "RGN005", 1400, "2002-12-15", "OPERATING",     "우라늄","한국수력원자력",     11),
    ("PLT008", "인천복합화력", "복합화력","RGN001", 900,  "2010-08-22", "OPERATING",     "LNG",  "한국서부발전",       370),
    ("PLT009", "경기태양광",   "태양광",  "RGN001", 150,  "2020-05-18", "OPERATING",     "태양열","한국남동발전",       None),
    ("PLT010", "강원수력",     "수력",    "RGN002", 300,  "1975-03-01", "OPERATING",     "수력", "한국수력원자력",     None),
    ("PLT011", "전북풍력",     "풍력",    "RGN004", 180,  "2019-11-28", "MAINTENANCE",   "바람", "한국남부발전",       None),
    ("PLT012", "울산화력",     "화력",    "RGN009", 750,  "1995-04-20", "OPERATING",     "LNG",  "한국동서발전",       490),
]

PLANT_STATUSES = ["OPERATING", "MAINTENANCE", "STANDBY", "DECOMMISSIONED"]

METER_DEFS = [
    ("MTR001", "서울강남산업단지", "산업용", "RGN001", "제조업",   50000, "154kV",  "2010-01-15", "ACTIVE"),
    ("MTR002", "인천항만물류센터", "산업용", "RGN001", "제조업",   30000, "22.9kV", "2012-06-20", "ACTIVE"),
    ("MTR003", "수원전자공단",     "산업용", "RGN001", "제조업",   80000, "154kV",  "2008-03-10", "ACTIVE"),
    ("MTR004", "강원관광단지",     "상업용", "RGN002", "서비스업",  5000, "22.9kV", "2015-07-01", "ACTIVE"),
    ("MTR005", "청주오창산업단지", "산업용", "RGN003", "제조업",   60000, "154kV",  "2011-09-15", "ACTIVE"),
    ("MTR006", "대전엑스포단지",   "상업용", "RGN003", "서비스업",  8000, "22.9kV", "2013-04-22", "ACTIVE"),
    ("MTR007", "광주첨단산단",     "산업용", "RGN004", "제조업",   45000, "154kV",  "2009-11-30", "ACTIVE"),
    ("MTR008", "전주혁신도시",     "상업용", "RGN004", "공공기관",  3000, "22.9kV", "2017-02-14", "ACTIVE"),
    ("MTR009", "포항철강단지",     "산업용", "RGN005", "제조업",  100000, "154kV",  "2000-05-20", "ACTIVE"),
    ("MTR010", "경주관광지구",     "상업용", "RGN005", "서비스업",  2000, "22.9kV", "2014-08-11", "ACTIVE"),
    ("MTR011", "창원기계산업단지", "산업용", "RGN006", "제조업",   70000, "154kV",  "2005-12-01", "ACTIVE"),
    ("MTR012", "진주혁신도시",     "상업용", "RGN006", "공공기관",  4000, "22.9kV", "2016-03-25", "ACTIVE"),
    ("MTR013", "부산항국제터미널", "산업용", "RGN007", "제조업",   35000, "154kV",  "2007-10-18", "ACTIVE"),
    ("MTR014", "해운대관광특구",   "상업용", "RGN007", "서비스업",  6000, "22.9kV", "2012-05-30", "ACTIVE"),
    ("MTR015", "제주첨단과학단지", "상업용", "RGN008", "서비스업",  1500, "22.9kV", "2018-09-05", "ACTIVE"),
    ("MTR016", "제주주거단지A",    "주거용", "RGN008", "주거단지",   500, "380V",   "2019-01-20", "ACTIVE"),
    ("MTR017", "울산석유화학단지", "산업용", "RGN009", "제조업",  120000, "154kV",  "1998-07-12", "ACTIVE"),
    ("MTR018", "울산주거단지B",    "주거용", "RGN009", "주거단지",   800, "220V",   "2015-11-10", "ACTIVE"),
    ("MTR019", "수도권변전소A",    "변전소", "RGN001", "공공기관", 200000, "154kV",  "2003-04-15", "ACTIVE"),
    ("MTR020", "경기주거단지C",    "주거용", "RGN001", "주거단지",  1200, "220V",   "2016-08-22", "FAULTY"),
]

OUTAGE_TYPES = ["계획정전", "강제정전", "자연재해", "설비고장", "수요초과"]

CAUSE_DESCRIPTIONS = {
    "계획정전": [
        "정기 설비 점검 및 보수 작업",
        "송전선로 교체 공사",
        "변전소 변압기 교체 작업",
        "케이블 노후화로 인한 예방 교체",
        "안전 점검 의무 이행",
    ],
    "강제정전": [
        "변압기 과부하로 인한 트립",
        "차단기 오작동으로 인한 정전",
        "지하케이블 절연 파괴",
        "연결 접속부 과열로 인한 단락",
        "보호계전기 오동작",
    ],
    "자연재해": [
        "태풍으로 인한 송전탑 도복",
        "집중호우로 인한 지하설비 침수",
        "낙뢰로 인한 절연체 파손",
        "강풍으로 인한 전선 단선",
        "폭설로 인한 전선 단선 및 설비 파손",
    ],
    "설비고장": [
        "변압기 내부 절연유 열화",
        "개폐기 접촉 불량",
        "송전선 코로나 방전 이상",
        "케이블 접속 불량으로 인한 과열",
        "계기용 변성기 고장",
    ],
    "수요초과": [
        "하계 냉방 수요 급증으로 예비율 부족",
        "동계 한파 난방 수요 집중",
        "피크 시간대 수요 예측 초과",
        "예비력 부족으로 인한 부하 차단",
        "계통 주파수 저하로 인한 긴급 부하 차단",
    ],
}

RESTORATION_METHODS = [
    "복구반 현장 출동 후 설비 수리",
    "예비 변압기 절체",
    "우회 송전 경로 전환",
    "긴급 복구팀 투입 및 임시 설비 가동",
    "자동 재투입 장치 동작",
    "이동형 발전기 투입",
]


# ---------------------------------------------------------------------------
# MST_REGION
# ---------------------------------------------------------------------------

def generate_mst_region():
    fields = ["REGION_ID", "REGION_NAME", "REGION_TYPE", "POPULATION_MILLION",
              "PEAK_DEMAND_MW", "GRID_ZONE"]
    rows = []
    for r in REGIONS:
        rows.append({
            "REGION_ID":           r[0],
            "REGION_NAME":         r[1],
            "REGION_TYPE":         r[2],
            "POPULATION_MILLION":  r[3],
            "PEAK_DEMAND_MW":      r[4],
            "GRID_ZONE":           r[5],
        })
    write_csv("MST_REGION.csv", fields, rows)
    return {r[0] for r in REGIONS}


# ---------------------------------------------------------------------------
# MST_PLANT
# ---------------------------------------------------------------------------

def generate_mst_plant():
    fields = ["PLANT_ID", "PLANT_NAME", "PLANT_TYPE", "REGION_ID", "CAPACITY_MW",
              "COMMISSION_DATE", "STATUS", "FUEL_TYPE", "OPERATOR_NAME",
              "CO2_EMISSION_FACTOR"]
    rows = []
    for p in PLANTS_RAW:
        rows.append({
            "PLANT_ID":             p[0],
            "PLANT_NAME":           p[1],
            "PLANT_TYPE":           p[2],
            "REGION_ID":            p[3],
            "CAPACITY_MW":          p[4],
            "COMMISSION_DATE":      p[5],
            "STATUS":               p[6],
            "FUEL_TYPE":            p[7],
            "OPERATOR_NAME":        p[8],
            "CO2_EMISSION_FACTOR":  p[9],  # None for renewables already set
        })
    write_csv("MST_PLANT.csv", fields, rows)
    return [p[0] for p in PLANTS_RAW]


# ---------------------------------------------------------------------------
# MST_METER
# ---------------------------------------------------------------------------

def generate_mst_meter():
    fields = ["METER_ID", "METER_NAME", "METER_TYPE", "REGION_ID", "CUSTOMER_TYPE",
              "CONTRACT_CAPACITY_KW", "VOLTAGE_LEVEL", "INSTALL_DATE", "STATUS"]
    rows = []
    for m in METER_DEFS:
        rows.append({
            "METER_ID":              m[0],
            "METER_NAME":            m[1],
            "METER_TYPE":            m[2],
            "REGION_ID":             m[3],
            "CUSTOMER_TYPE":         m[4],
            "CONTRACT_CAPACITY_KW":  m[5],
            "VOLTAGE_LEVEL":         m[6],
            "INSTALL_DATE":          m[7],
            "STATUS":                m[8],
        })
    write_csv("MST_METER.csv", fields, rows)
    return [m[0] for m in METER_DEFS]


# ---------------------------------------------------------------------------
# FACT_DAILY_USAGE
# ---------------------------------------------------------------------------

def _seasonal_factor(d: date, meter_type: str) -> float:
    month = d.month
    is_summer = 6 <= month <= 8
    is_winter = month == 12 or month <= 2
    is_weekday = d.weekday() < 5  # Mon-Fri

    if meter_type == "산업용":
        # Industrial: stable, mild seasonality
        if is_summer:
            factor = random.uniform(1.05, 1.15)
        elif is_winter:
            factor = random.uniform(1.05, 1.12)
        else:
            factor = random.uniform(0.95, 1.05)
        # Slight weekday bump
        if is_weekday:
            factor *= random.uniform(1.02, 1.08)
        else:
            factor *= random.uniform(0.85, 0.95)
    elif meter_type == "상업용":
        if is_summer:
            factor = random.uniform(1.4, 1.8)
        elif is_winter:
            factor = random.uniform(1.3, 1.6)
        else:
            factor = random.uniform(0.9, 1.1)
        if is_weekday:
            factor *= 1.2
        else:
            factor *= 0.75
    elif meter_type == "주거용":
        if is_summer:
            factor = random.uniform(1.3, 1.6)
        elif is_winter:
            factor = random.uniform(1.4, 1.7)
        else:
            factor = random.uniform(0.85, 1.05)
        # Weekends slightly higher for residential
        if not is_weekday:
            factor *= random.uniform(1.05, 1.15)
    else:  # 변전소
        if is_summer:
            factor = random.uniform(1.3, 1.5)
        elif is_winter:
            factor = random.uniform(1.2, 1.4)
        else:
            factor = random.uniform(0.9, 1.1)

    return factor


def generate_fact_daily_usage(meter_ids: list):
    fields = ["USAGE_ID", "METER_ID", "USAGE_DATE", "USAGE_KWH", "PEAK_KW",
              "OFFPEAK_KW", "REACTIVE_KVARH", "POWER_FACTOR", "IS_PEAK_DAY",
              "ESTIMATED_FLAG"]
    rows = []
    usage_id = 1

    start = date(2023, 1, 1)
    end   = date(2024, 12, 31)

    # Base usage per meter (kWh/day) roughly proportional to contract capacity
    base_daily = {m[0]: m[5] * random.uniform(0.10, 0.18) for m in METER_DEFS}

    # Peak days: weekdays in summer (Jun-Aug) and winter (Dec-Feb)
    def is_peak_day(d: date) -> bool:
        if d.weekday() >= 5:
            return False
        return (6 <= d.month <= 8) or (d.month == 12) or (d.month <= 2)

    meter_type_map = {m[0]: m[2] for m in METER_DEFS}

    for d in date_range(start, end):
        for mid in meter_ids:
            mtype = meter_type_map[mid]
            base  = base_daily[mid]
            factor = _seasonal_factor(d, mtype)
            usage  = base * factor

            # Anomaly: 2% spike (equipment malfunction)
            if random.random() < 0.02:
                usage *= random.uniform(2.0, 3.0)
            # Anomaly: 1% near-zero (outage)
            elif random.random() < 0.01:
                usage *= random.uniform(0.01, 0.08)

            usage = round(usage, 2)

            # Peak / offpeak split (60/40)
            peak_kwh    = round(usage * random.uniform(0.55, 0.65), 2)
            offpeak_kwh = round(usage - peak_kwh, 2)

            # Peak KW (demand)
            peak_kw = round(usage / random.uniform(18, 22), 2)
            offpeak_kw = round(offpeak_kwh / random.uniform(10, 14), 2)

            # Reactive power
            reactive = round(usage * random.uniform(0.05, 0.25), 2)

            # Power factor (15% NULL)
            pf = nullable(round(random.uniform(0.85, 0.99), 3), 0.15)

            is_pk = is_peak_day(d)
            estimated = "Y" if random.random() < 0.05 else "N"

            rows.append({
                "USAGE_ID":       usage_id,
                "METER_ID":       mid,
                "USAGE_DATE":     fmt_date(d),
                "USAGE_KWH":      usage,
                "PEAK_KW":        peak_kw,
                "OFFPEAK_KW":     offpeak_kw,
                "REACTIVE_KVARH": reactive,
                "POWER_FACTOR":   pf,
                "IS_PEAK_DAY":    1 if is_pk else 0,
                "ESTIMATED_FLAG": estimated,
            })
            usage_id += 1

    write_csv("FACT_DAILY_USAGE.csv", fields, rows)


# ---------------------------------------------------------------------------
# FACT_MONTHLY_BILL
# ---------------------------------------------------------------------------

def generate_fact_monthly_bill(meter_ids: list):
    fields = ["BILL_ID", "METER_ID", "YEAR_MONTH", "USAGE_KWH", "PEAK_USAGE_KWH",
              "OFFPEAK_USAGE_KWH", "DEMAND_CHARGE_KRW", "ENERGY_CHARGE_KRW",
              "FUEL_ADJUSTMENT_KRW", "TAX_KRW", "TOTAL_BILL_KRW",
              "PAYMENT_DATE", "PAYMENT_STATUS"]
    rows = []
    bill_id = 1

    # Fuel adjustment rate per month (can be negative): ±15원/kWh
    fuel_adj_rates = {}
    for year in [2022, 2023, 2024]:
        for month in range(1, 13):
            fuel_adj_rates[(year, month)] = round(random.uniform(-15.0, 15.0), 2)

    contract_capacity = {m[0]: m[5] for m in METER_DEFS}

    # Seasonal multiplier for monthly usage
    def monthly_factor(month: int, mtype: str) -> float:
        is_summer = 6 <= month <= 8
        is_winter = month == 12 or month <= 2
        if mtype == "산업용":
            if is_summer: return random.uniform(1.05, 1.12)
            if is_winter: return random.uniform(1.03, 1.10)
            return random.uniform(0.95, 1.05)
        elif mtype == "상업용":
            if is_summer: return random.uniform(1.35, 1.70)
            if is_winter: return random.uniform(1.25, 1.55)
            return random.uniform(0.85, 1.10)
        elif mtype == "주거용":
            if is_summer: return random.uniform(1.25, 1.55)
            if is_winter: return random.uniform(1.35, 1.65)
            return random.uniform(0.80, 1.05)
        else:  # 변전소
            if is_summer: return random.uniform(1.20, 1.45)
            if is_winter: return random.uniform(1.15, 1.40)
            return random.uniform(0.90, 1.10)

    meter_type_map = {m[0]: m[2] for m in METER_DEFS}

    for year in [2022, 2023, 2024]:
        for month in range(1, 13):
            ym = f"{year}-{month:02d}"
            for mid in meter_ids:
                mtype = meter_type_map[mid]
                cap   = contract_capacity[mid]
                days_in_month = 30  # approximate

                base_daily = cap * random.uniform(0.10, 0.18)
                factor = monthly_factor(month, mtype)
                usage  = round(base_daily * factor * days_in_month, 1)

                # Peak/offpeak split
                peak_usage    = round(usage * random.uniform(0.55, 0.65), 1)
                offpeak_usage = round(usage - peak_usage, 1)

                # Tariff calculation
                demand_charge  = round(cap * 7220, 0)
                energy_charge  = round(peak_usage * 164 + offpeak_usage * 98, 0)
                fuel_adj_rate  = fuel_adj_rates[(year, month)]
                fuel_adj       = round(usage * fuel_adj_rate, 0)

                subtotal = demand_charge + energy_charge + fuel_adj
                tax      = round(subtotal * 0.10, 0)
                total    = round(subtotal + tax, 0)

                # Payment status (~10% unpaid)
                rand_pay = random.random()
                if rand_pay < 0.07:
                    payment_status = "UNPAID"
                    payment_date   = None
                elif rand_pay < 0.10:
                    payment_status = "OVERDUE"
                    payment_date   = None
                elif rand_pay < 0.12:
                    payment_status = "PARTIAL"
                    # partial payment date exists
                    pay_d = date(year, month, 1) + timedelta(days=random.randint(20, 50))
                    payment_date = fmt_date(pay_d)
                else:
                    payment_status = "PAID"
                    pay_d = date(year, month, 1) + timedelta(days=random.randint(15, 45))
                    payment_date = fmt_date(pay_d)

                rows.append({
                    "BILL_ID":              bill_id,
                    "METER_ID":             mid,
                    "YEAR_MONTH":           ym,
                    "USAGE_KWH":            usage,
                    "PEAK_USAGE_KWH":       peak_usage,
                    "OFFPEAK_USAGE_KWH":    offpeak_usage,
                    "DEMAND_CHARGE_KRW":    demand_charge,
                    "ENERGY_CHARGE_KRW":    energy_charge,
                    "FUEL_ADJUSTMENT_KRW":  fuel_adj,
                    "TAX_KRW":              tax,
                    "TOTAL_BILL_KRW":       total,
                    "PAYMENT_DATE":         payment_date,
                    "PAYMENT_STATUS":       payment_status,
                })
                bill_id += 1

    write_csv("FACT_MONTHLY_BILL.csv", fields, rows)


# ---------------------------------------------------------------------------
# FACT_OUTAGE
# ---------------------------------------------------------------------------

def generate_fact_outage(plant_ids: list, region_ids: set):
    fields = ["OUTAGE_ID", "PLANT_ID", "REGION_ID", "OUTAGE_DATE", "START_TIME",
              "END_TIME", "DURATION_HOURS", "OUTAGE_TYPE", "AFFECTED_CUSTOMERS",
              "ENERGY_NOT_SUPPLIED_MWH", "CAUSE_DESCRIPTION", "RESTORATION_METHOD",
              "COST_KRW"]

    region_list = sorted(region_ids)
    rows = []

    # Distribution: 60 계획, 30 강제, 25 자연재해, 25 설비고장, 10 수요초과 = 150
    outage_plan = [
        ("계획정전",  60, (2.0,  8.0)),
        ("강제정전",  30, (4.0, 24.0)),
        ("자연재해",  25, (8.0, 72.0)),
        ("설비고장",  25, (2.0, 48.0)),
        ("수요초과",  10, (0.5,  2.0)),
    ]

    outage_id = 1
    all_dates = list(date_range(date(2022, 1, 1), date(2024, 12, 31)))
    typhoon_dates = [d for d in all_dates if 7 <= d.month <= 9]
    peak_dates    = [d for d in all_dates if
                     (6 <= d.month <= 8 or d.month == 12 or d.month <= 2)
                     and d.weekday() < 5]

    for otype, count, (dur_min, dur_max) in outage_plan:
        for _ in range(count):
            # Date selection by type
            if otype == "자연재해":
                outage_date = random.choice(typhoon_dates)
            elif otype == "수요초과":
                outage_date = random.choice(peak_dates)
            else:
                outage_date = random.choice(all_dates)

            duration = round(random.uniform(dur_min, dur_max), 2)

            # Start time
            start_hour = random.randint(0, 23)
            start_min  = random.choice([0, 15, 30, 45])
            start_dt   = datetime(outage_date.year, outage_date.month, outage_date.day,
                                   start_hour, start_min)
            end_dt     = start_dt + timedelta(hours=duration)
            start_time = start_dt.strftime("%H:%M")
            end_time   = end_dt.strftime("%H:%M")

            # Plant ID: nullable ~35% (distribution-side outages)
            plant_id = nullable(random.choice(plant_ids), 0.35)
            region_id = random.choice(region_list)

            # Affected customers
            affected = random.randint(50, 50000)

            # Energy not supplied (MWh)
            ens = round(duration * random.uniform(10, 500), 1)

            cause = random.choice(CAUSE_DESCRIPTIONS[otype])
            restoration = random.choice(RESTORATION_METHODS)

            # Cost ~20% NULL
            cost = nullable(round(random.uniform(5_000_000, 2_000_000_000), 0), 0.20)

            rows.append({
                "OUTAGE_ID":                outage_id,
                "PLANT_ID":                 plant_id,
                "REGION_ID":                region_id,
                "OUTAGE_DATE":              fmt_date(outage_date),
                "START_TIME":               start_time,
                "END_TIME":                 end_time,
                "DURATION_HOURS":           duration,
                "OUTAGE_TYPE":              otype,
                "AFFECTED_CUSTOMERS":       affected,
                "ENERGY_NOT_SUPPLIED_MWH":  ens,
                "CAUSE_DESCRIPTION":        cause,
                "RESTORATION_METHOD":       restoration,
                "COST_KRW":                 cost,
            })
            outage_id += 1

    # Shuffle so types are interleaved
    random.shuffle(rows)
    # Re-assign sequential IDs after shuffle
    for i, row in enumerate(rows, 1):
        row["OUTAGE_ID"] = i

    write_csv("FACT_OUTAGE.csv", fields, rows)


# ---------------------------------------------------------------------------
# SCHEMA_DEFINITION.json
# ---------------------------------------------------------------------------

SCHEMA = {
    "domain": "전력·가스 유틸리티 운영",
    "generated_at": "2025-01-01",
    "tables": {
        "MST_REGION": {
            "description": "지역 마스터 (9개 권역)",
            "primary_key": "REGION_ID",
            "columns": {
                "REGION_ID":          {"type": "VARCHAR(6)",  "nullable": False, "description": "지역 고유 ID"},
                "REGION_NAME":        {"type": "VARCHAR(20)", "nullable": False, "description": "지역명"},
                "REGION_TYPE":        {"type": "VARCHAR(10)", "nullable": False, "description": "광역시/도 구분"},
                "POPULATION_MILLION": {"type": "DECIMAL(5,1)","nullable": False, "description": "인구 (백만명)"},
                "PEAK_DEMAND_MW":     {"type": "INTEGER",     "nullable": False, "description": "최대 수요 (MW)"},
                "GRID_ZONE":          {"type": "VARCHAR(10)", "nullable": False, "description": "계통 구역 (수도권/남부/북부)"},
            }
        },
        "MST_PLANT": {
            "description": "발전소 마스터 (12개소)",
            "primary_key": "PLANT_ID",
            "foreign_keys": {"REGION_ID": "MST_REGION.REGION_ID"},
            "columns": {
                "PLANT_ID":             {"type": "VARCHAR(6)",  "nullable": False},
                "PLANT_NAME":           {"type": "VARCHAR(30)", "nullable": False},
                "PLANT_TYPE":           {"type": "VARCHAR(10)", "nullable": False, "values": ["화력","원자력","태양광","풍력","수력","복합화력"]},
                "REGION_ID":            {"type": "VARCHAR(6)",  "nullable": False, "fk": "MST_REGION.REGION_ID"},
                "CAPACITY_MW":          {"type": "INTEGER",     "nullable": False},
                "COMMISSION_DATE":      {"type": "DATE",        "nullable": False},
                "STATUS":               {"type": "VARCHAR(15)", "nullable": False, "values": ["OPERATING","MAINTENANCE","STANDBY","DECOMMISSIONED"]},
                "FUEL_TYPE":            {"type": "VARCHAR(10)", "nullable": False, "values": ["LNG","석탄","우라늄","태양열","바람","수력"]},
                "OPERATOR_NAME":        {"type": "VARCHAR(30)", "nullable": False},
                "CO2_EMISSION_FACTOR":  {"type": "INTEGER",     "nullable": True,  "description": "gCO2/kWh, 재생에너지는 NULL"},
            }
        },
        "MST_METER": {
            "description": "계량기 마스터 (20개소)",
            "primary_key": "METER_ID",
            "foreign_keys": {"REGION_ID": "MST_REGION.REGION_ID"},
            "columns": {
                "METER_ID":              {"type": "VARCHAR(6)",  "nullable": False},
                "METER_NAME":            {"type": "VARCHAR(30)", "nullable": False},
                "METER_TYPE":            {"type": "VARCHAR(10)", "nullable": False, "values": ["산업용","상업용","주거용","변전소"]},
                "REGION_ID":             {"type": "VARCHAR(6)",  "nullable": False, "fk": "MST_REGION.REGION_ID"},
                "CUSTOMER_TYPE":         {"type": "VARCHAR(10)", "nullable": False, "values": ["제조업","서비스업","주거단지","공공기관"]},
                "CONTRACT_CAPACITY_KW":  {"type": "INTEGER",     "nullable": False},
                "VOLTAGE_LEVEL":         {"type": "VARCHAR(10)", "nullable": False, "values": ["154kV","22.9kV","380V","220V"]},
                "INSTALL_DATE":          {"type": "DATE",        "nullable": False},
                "STATUS":                {"type": "VARCHAR(10)", "nullable": False, "values": ["ACTIVE","INACTIVE","FAULTY"]},
            }
        },
        "FACT_DAILY_USAGE": {
            "description": "일별 전력 사용량 (2023-01-01 ~ 2024-12-31, 20계량기 × 730일 = 14,600행)",
            "primary_key": "USAGE_ID",
            "foreign_keys": {"METER_ID": "MST_METER.METER_ID"},
            "columns": {
                "USAGE_ID":       {"type": "INTEGER",     "nullable": False},
                "METER_ID":       {"type": "VARCHAR(6)",  "nullable": False, "fk": "MST_METER.METER_ID"},
                "USAGE_DATE":     {"type": "DATE",        "nullable": False},
                "USAGE_KWH":      {"type": "DECIMAL(12,2)","nullable": False, "description": "당일 총 사용량 (kWh)"},
                "PEAK_KW":        {"type": "DECIMAL(10,2)","nullable": False, "description": "최대 수요전력 (kW)"},
                "OFFPEAK_KW":     {"type": "DECIMAL(10,2)","nullable": False},
                "REACTIVE_KVARH": {"type": "DECIMAL(10,2)","nullable": False},
                "POWER_FACTOR":   {"type": "DECIMAL(4,3)", "nullable": True,  "description": "역률, ~15% NULL"},
                "IS_PEAK_DAY":    {"type": "BOOLEAN",     "nullable": False,  "description": "피크 시즌 평일 여부"},
                "ESTIMATED_FLAG": {"type": "CHAR(1)",     "nullable": False,  "description": "Y=추정검침, N=실검침, 5% Y"},
            }
        },
        "FACT_MONTHLY_BILL": {
            "description": "월별 청구서 (2022-01 ~ 2024-12, 36개월 × 20계량기 = 720행)",
            "primary_key": "BILL_ID",
            "foreign_keys": {"METER_ID": "MST_METER.METER_ID"},
            "columns": {
                "BILL_ID":              {"type": "INTEGER",      "nullable": False},
                "METER_ID":             {"type": "VARCHAR(6)",   "nullable": False, "fk": "MST_METER.METER_ID"},
                "YEAR_MONTH":           {"type": "CHAR(7)",      "nullable": False, "description": "YYYY-MM"},
                "USAGE_KWH":            {"type": "DECIMAL(12,1)","nullable": False},
                "PEAK_USAGE_KWH":       {"type": "DECIMAL(12,1)","nullable": False},
                "OFFPEAK_USAGE_KWH":    {"type": "DECIMAL(12,1)","nullable": False},
                "DEMAND_CHARGE_KRW":    {"type": "BIGINT",       "nullable": False, "description": "기본요금 = 계약전력×7,220원/kW"},
                "ENERGY_CHARGE_KRW":    {"type": "BIGINT",       "nullable": False, "description": "전력량요금 (최대부하 164원, 경부하 98원)"},
                "FUEL_ADJUSTMENT_KRW":  {"type": "BIGINT",       "nullable": False, "description": "연료비조정요금 (±15원/kWh, 음수 가능)"},
                "TAX_KRW":              {"type": "BIGINT",       "nullable": False, "description": "부가세 10%"},
                "TOTAL_BILL_KRW":       {"type": "BIGINT",       "nullable": False},
                "PAYMENT_DATE":         {"type": "DATE",         "nullable": True,  "description": "~10% NULL (미납)"},
                "PAYMENT_STATUS":       {"type": "VARCHAR(10)",  "nullable": False, "values": ["PAID","UNPAID","OVERDUE","PARTIAL"]},
            }
        },
        "FACT_OUTAGE": {
            "description": "정전 이벤트 (2022-2024, 약 150건)",
            "primary_key": "OUTAGE_ID",
            "foreign_keys": {
                "PLANT_ID":  "MST_PLANT.PLANT_ID",
                "REGION_ID": "MST_REGION.REGION_ID",
            },
            "columns": {
                "OUTAGE_ID":               {"type": "INTEGER",      "nullable": False},
                "PLANT_ID":                {"type": "VARCHAR(6)",   "nullable": True,  "description": "~35% NULL (배전측 정전)"},
                "REGION_ID":               {"type": "VARCHAR(6)",   "nullable": False, "fk": "MST_REGION.REGION_ID"},
                "OUTAGE_DATE":             {"type": "DATE",         "nullable": False},
                "START_TIME":              {"type": "TIME",         "nullable": False},
                "END_TIME":                {"type": "TIME",         "nullable": False},
                "DURATION_HOURS":          {"type": "DECIMAL(5,2)", "nullable": False},
                "OUTAGE_TYPE":             {"type": "VARCHAR(10)",  "nullable": False, "values": ["계획정전","강제정전","자연재해","설비고장","수요초과"]},
                "AFFECTED_CUSTOMERS":      {"type": "INTEGER",      "nullable": False},
                "ENERGY_NOT_SUPPLIED_MWH": {"type": "DECIMAL(8,1)", "nullable": False},
                "CAUSE_DESCRIPTION":       {"type": "VARCHAR(100)", "nullable": False},
                "RESTORATION_METHOD":      {"type": "VARCHAR(100)", "nullable": False},
                "COST_KRW":                {"type": "BIGINT",       "nullable": True,  "description": "~20% NULL"},
            }
        },
    },
    "relationships": [
        {"from": "MST_PLANT.REGION_ID",      "to": "MST_REGION.REGION_ID"},
        {"from": "MST_METER.REGION_ID",      "to": "MST_REGION.REGION_ID"},
        {"from": "FACT_DAILY_USAGE.METER_ID","to": "MST_METER.METER_ID"},
        {"from": "FACT_MONTHLY_BILL.METER_ID","to": "MST_METER.METER_ID"},
        {"from": "FACT_OUTAGE.PLANT_ID",     "to": "MST_PLANT.PLANT_ID"},
        {"from": "FACT_OUTAGE.REGION_ID",    "to": "MST_REGION.REGION_ID"},
    ]
}


LOGIC_DOC = """\
================================================================
전력·가스 유틸리티 운영 관리 전략 문서
작성 기준: 2025년 전력 운영 정책
================================================================

1. 수요 예측 및 부하 관리
   - 계절성 수요 패턴: 하계 냉방(6~8월), 동계 난방(12~2월) 피크
   - 일부하 곡선: 아침 피크(08~10시), 저녁 피크(18~21시)
   - 계시별 요금제: 최대부하/중간부하/경부하 시간대 구분
   - 수요반응(DR): 피크 시 산업용 고객 부하 감축 유도

2. 발전원별 운영 전략
   - 기저발전: 원자력, 석탄 (24시간 상시 운전)
   - 첨두발전: LNG 복합화력 (피크 시 기동)
   - 재생에너지: 태양광(주간), 풍력(간헐적) - 출력 예측 필요
   - 수력: 저수량에 따른 계절적 운용

3. 피크 관리 기준
   - 최대전력 수요 초과 위험 (예비율 < 10%): 비상 DR 발동
   - 하계 피크: 7월 중순 ~ 8월 중순 평일 14~17시
   - 동계 피크: 1월 한파 시 오전 9~11시
   - 피크저감 목표: 전년 동기 대비 5% 감축

4. 정전 관리 및 복구 기준
   - 계획정전: 30일 전 고객 통보, 4시간 이내 복구
   - 강제정전: 즉시 복구 체계 가동, 24시간 내 복구 목표
   - 자연재해: 재난안전법에 따른 비상복구팀 투입
   - SAIDI (고객 평균 정전시간): 연 60분 이하 목표

5. 요금 체계 및 KPI
   - 기본요금: 계약전력 × 7,220원/kW
   - 전력량 요금: 최대부하 164원, 중간 119원, 경부하 98원
   - 연료비 조정요금: 원가 변동에 따라 분기별 조정
   - 수금률: 98% 이상 목표, 연체 3개월 시 단전 조치

6. 재생에너지 통합 관리
   - REC(신재생에너지 공급인증서) 발급 및 거래
   - 출력 변동성 보완: ESS(에너지저장시스템) 운용
   - 계통 안정성: 재생에너지 비중 30% 이상 시 안정화 조치

7. KPI
   - 발전 가동률: 화력 85%, 원자력 90% 이상
   - 설비 이용률: 태양광 15%, 풍력 25% (이용률 특성 반영)
   - 고객 정전 경험률: 연 1회 이하
   - 온실가스 배출 집약도: 연간 5% 감축 목표
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Energy Utility Demo Data Generator ===")
    os.makedirs(DATA_DIR, exist_ok=True)

    print("\n[1/6] MST_REGION")
    region_ids = generate_mst_region()

    print("\n[2/6] MST_PLANT")
    plant_ids = generate_mst_plant()

    print("\n[3/6] MST_METER")
    meter_ids = generate_mst_meter()

    print("\n[4/6] FACT_DAILY_USAGE  (14,600 rows - may take a moment)")
    generate_fact_daily_usage(meter_ids)

    print("\n[5/6] FACT_MONTHLY_BILL (720 rows)")
    generate_fact_monthly_bill(meter_ids)

    print("\n[6/6] FACT_OUTAGE       (150 rows)")
    generate_fact_outage(plant_ids, region_ids)

    # Write SCHEMA_DEFINITION.json
    schema_path = os.path.join(DATA_DIR, "SCHEMA_DEFINITION.json")
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(SCHEMA, f, ensure_ascii=False, indent=2)
    print(f"\n  Wrote schema -> {schema_path}")

    # Write LOGIC_DOCUMENT.txt
    logic_path = os.path.join(DATA_DIR, "LOGIC_DOCUMENT.txt")
    with open(logic_path, "w", encoding="utf-8") as f:
        f.write(LOGIC_DOC)
    print(f"  Wrote logic doc -> {logic_path}")

    print("\n=== Done ===")
