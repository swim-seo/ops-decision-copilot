"""
물류·배송 운영 관리 데모 데이터 생성기

테이블:
  - MST_HUB          : 물류 허브 마스터 (8개)
  - MST_VEHICLE      : 차량 마스터 (25대)
  - MST_ROUTE        : 노선 마스터 (20개)
  - FACT_DELIVERY    : 배송 실적 (~15,000건, 2023-2024)
  - FACT_DELAY       : 지연 이벤트 (~3,000건, 2023-2024)
  - FACT_COST        : 월별 차량 비용 (36개월 × 25대, 2022-2024)
  - SCHEMA_DEFINITION.json
  - LOGIC_DOCUMENT.txt
"""

import csv
import json
import os
import random
from datetime import date, datetime, timedelta

random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "logistics")
os.makedirs(DATA_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# helper
# ═══════════════════════════════════════════════════════════════

def write_csv(filename, fieldnames, rows):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {len(rows):>6,} rows → {filename}")


def maybe_null(value, null_prob=0.20):
    """Return None with null_prob probability, else return value."""
    return None if random.random() < null_prob else value


def fmt_date(d):
    return d.strftime("%Y-%m-%d")


def fmt_time(h, m):
    return f"{h:02d}:{m:02d}"


# ═══════════════════════════════════════════════════════════════
# 1. MST_HUB
# ═══════════════════════════════════════════════════════════════

HUB_DATA = [
    # HUB_ID, HUB_NAME, HUB_TYPE, REGION, ADDRESS, CAPACITY_PACKAGES_DAILY, DOCK_COUNT, OPERATING_HOURS, MANAGER_NAME, STATUS
    ("HUB001", "서울 메가허브",     "메가허브",   "경기",   "경기도 고양시 덕양구 화중로 50",        120000, 48, "00:00-24:00", "김재원", "ACTIVE"),
    ("HUB002", "부산 지역허브",     "지역허브",   "경남",   "부산광역시 강서구 공항진입로 108",        60000, 24, "04:00-23:00", "이민준", "ACTIVE"),
    ("HUB003", "대구 지역허브",     "지역허브",   "경북",   "대구광역시 달성군 구지면 창리로 200",     45000, 18, "04:00-23:00", "박성훈", "ACTIVE"),
    ("HUB004", "광주 지역허브",     "지역허브",   "전남",   "광주광역시 광산구 하남산단6번로 107",     35000, 14, "05:00-22:00", "최지현", "ACTIVE"),
    ("HUB005", "대전 지역허브",     "지역허브",   "충남",   "대전광역시 유성구 산업단지북로 5",        40000, 16, "05:00-22:00", "정수빈", "ACTIVE"),
    ("HUB006", "인천 서브허브",     "서브허브",   "경기",   "인천광역시 중구 신항대로 200",            25000, 10, "06:00-22:00", "한동훈", "ACTIVE"),
    ("HUB007", "서울 동부 서브허브","서브허브",   "서울",   "서울특별시 강동구 성내로 77",             20000,  8, "06:00-22:00", "오세진", "EXPANSION"),
    ("HUB008", "경기 남부 서브허브","서브허브",   "경기",   "경기도 화성시 향남읍 발안산단1로 95",     18000,  8, "06:00-22:00", "윤하나", "ACTIVE"),
]

HUB_IDS = [r[0] for r in HUB_DATA]

MST_HUB_FIELDS = [
    "HUB_ID", "HUB_NAME", "HUB_TYPE", "REGION", "ADDRESS",
    "CAPACITY_PACKAGES_DAILY", "DOCK_COUNT", "OPERATING_HOURS",
    "MANAGER_NAME", "STATUS",
]


def build_mst_hub():
    rows = []
    for h in HUB_DATA:
        rows.append(dict(zip(MST_HUB_FIELDS, h)))
    return rows


# ═══════════════════════════════════════════════════════════════
# 2. MST_VEHICLE
# ═══════════════════════════════════════════════════════════════

DRIVER_NAMES = [
    "강민호", "권태양", "김도현", "김민재", "나성식",
    "노재현", "류한수", "문준호", "박성민", "백승재",
    "서준영", "성동일", "송경훈", "안재원", "양상현",
    "오영택", "우성진", "유재석", "이준기", "임현우",
    "장민수", "전성국", "정도영", "조현우", "최성훈",
]

VEHICLE_SPECS = [
    # (id_prefix_start, id_prefix_end, v_type, hub_ids, cap_kg, cap_vol, fuel, efficiency_range)
    ("VHC001", "VHC005", "5톤트럭",  ["HUB001", "HUB002", "HUB003", "HUB004", "HUB005"],
     5000, 25.0, "경유", (8.5, 11.0)),
    ("VHC006", "VHC010", "11톤트럭", ["HUB001", "HUB002"],
     11000, 52.0, "LNG", (5.0, 7.5)),
    ("VHC011", "VHC015", "1톤트럭",  ["HUB006", "HUB007", "HUB008", "HUB001", "HUB005"],
     1000, 4.5, "경유", (12.0, 15.0)),
    ("VHC016", "VHC018", "냉동차",   ["HUB001", "HUB002", "HUB003"],
     4000, 18.0, "경유", (7.0, 9.0)),
    ("VHC019", "VHC022", "오토바이", ["HUB007", "HUB006", "HUB008", "HUB001"],
     50, 0.1, "경유", (22.0, 30.0)),
    ("VHC023", "VHC025", "오토바이", ["HUB007", "HUB006", "HUB008"],   # 전기밴 = 오토바이 type overridden below
     500, 2.5, "전기", (18.0, 25.0)),
]

# override VHC023-025 type
ELECTRIC_VAN_IDS = {"VHC023", "VHC024", "VHC025"}

MST_VEHICLE_FIELDS = [
    "VEHICLE_ID", "VEHICLE_NAME", "VEHICLE_TYPE", "LICENSE_PLATE",
    "HUB_ID", "CAPACITY_KG", "CAPACITY_VOLUME_M3",
    "FUEL_TYPE", "FUEL_EFFICIENCY_KM_PER_L",
    "DRIVER_NAME", "STATUS", "PURCHASE_DATE", "MILEAGE_KM",
]

PLATE_PREFIXES = ["서울", "경기", "부산", "대구", "인천"]


def _make_plate():
    region = random.choice(PLATE_PREFIXES)
    num1 = random.randint(10, 99)
    alpha = random.choice("가나다라마바사아자차카타파하")
    num2 = random.randint(1000, 9999)
    return f"{region} {num1}{alpha} {num2}"


def build_mst_vehicle():
    rows = []
    idx = 0
    all_specs_expanded = []

    for spec in VEHICLE_SPECS:
        start_num = int(spec[0][3:])
        end_num = int(spec[1][3:])
        for n in range(start_num, end_num + 1):
            vid = f"VHC{n:03d}"
            hub_pool = spec[3]
            hub = hub_pool[(n - start_num) % len(hub_pool)]
            v_type = "전기밴" if vid in ELECTRIC_VAN_IDS else spec[2]
            fuel = spec[6]
            eff = round(random.uniform(*spec[7]), 1)
            cap_kg = spec[4]
            cap_vol = spec[5]
            driver = DRIVER_NAMES[idx % len(DRIVER_NAMES)]
            purchase_year = random.randint(2018, 2023)
            purchase_month = random.randint(1, 12)
            purchase_day = random.randint(1, 28)
            mileage = random.randint(5000, 180000)
            status_choices = (["ACTIVE"] * 9) + ["MAINTENANCE"]
            status = random.choice(status_choices)
            rows.append({
                "VEHICLE_ID": vid,
                "VEHICLE_NAME": f"{v_type} {n:03d}호",
                "VEHICLE_TYPE": v_type,
                "LICENSE_PLATE": _make_plate(),
                "HUB_ID": hub,
                "CAPACITY_KG": cap_kg,
                "CAPACITY_VOLUME_M3": cap_vol,
                "FUEL_TYPE": fuel,
                "FUEL_EFFICIENCY_KM_PER_L": eff,
                "DRIVER_NAME": driver,
                "STATUS": status,
                "PURCHASE_DATE": f"{purchase_year}-{purchase_month:02d}-{purchase_day:02d}",
                "MILEAGE_KM": mileage,
            })
            all_specs_expanded.append((vid, hub, cap_kg, cap_vol, fuel, eff))
            idx += 1

    return rows, all_specs_expanded  # rows + lookup list


# ═══════════════════════════════════════════════════════════════
# 3. MST_ROUTE
# ═══════════════════════════════════════════════════════════════

ROUTE_DEFS = [
    # ROUTE_ID, ROUTE_NAME, ORIGIN, DEST, DIST_KM, STD_HRS, ROUTE_TYPE, TOLL_KRW, VHC_TYPE_REQ, FREQUENCY, STATUS
    ("RTE001", "서울→부산 간선",         "HUB001", "HUB002", 430, 5.5,  "간선",       38500, "11톤트럭",  "일 1회",  "ACTIVE"),
    ("RTE002", "서울→대구 간선",         "HUB001", "HUB003", 290, 3.5,  "간선",       26000, "11톤트럭",  "일 1회",  "ACTIVE"),
    ("RTE003", "서울→광주 간선",         "HUB001", "HUB004", 350, 4.5,  "간선",       31500, "11톤트럭",  "일 1회",  "ACTIVE"),
    ("RTE004", "서울→대전 간선",         "HUB001", "HUB005", 150, 2.0,  "간선",       12000, "11톤트럭",  "일 2회",  "ACTIVE"),
    ("RTE005", "부산→창원 지선",         "HUB002", "HUB002", 55,  1.0,  "지선",        4500, "5톤트럭",   "일 2회",  "ACTIVE"),
    ("RTE006", "대구→포항 지선",         "HUB003", "HUB003", 80,  1.5,  "지선",        6200, "5톤트럭",   "일 1회",  "ACTIVE"),
    ("RTE007", "대전→천안 지선",         "HUB005", "HUB005", 70,  1.2,  "지선",        5500, "5톤트럭",   "일 2회",  "ACTIVE"),
    ("RTE008", "광주→목포 지선",         "HUB004", "HUB004", 90,  1.5,  "지선",        7000, "5톤트럭",   "주 3회",  "ACTIVE"),
    ("RTE009", "서울→인천 지선",         "HUB001", "HUB006", 40,  0.8,  "지선",        2500, "5톤트럭",   "일 2회",  "ACTIVE"),
    ("RTE010", "서울→동부 지선",         "HUB001", "HUB007", 25,  0.7,  "지선",        1500, "5톤트럭",   "일 2회",  "ACTIVE"),
    ("RTE011", "서울→경기남부 지선",     "HUB001", "HUB008", 60,  1.0,  "지선",        4800, "5톤트럭",   "일 1회",  "ACTIVE"),
    ("RTE012", "서울 도심 라스트마일 A", "HUB007", "HUB007", 15,  1.5,  "라스트마일",     0, "1톤트럭",   "일 2회",  "ACTIVE"),
    ("RTE013", "서울 도심 라스트마일 B", "HUB007", "HUB007", 12,  1.2,  "라스트마일",     0, "오토바이",  "탄력운행", "ACTIVE"),
    ("RTE014", "인천 도심 라스트마일",   "HUB006", "HUB006", 18,  1.8,  "라스트마일",     0, "1톤트럭",   "일 2회",  "ACTIVE"),
    ("RTE015", "경기남부 라스트마일",    "HUB008", "HUB008", 20,  2.0,  "라스트마일",     0, "1톤트럭",   "일 1회",  "ACTIVE"),
    ("RTE016", "부산항 국제선",          "HUB002", "HUB006", 480, 6.0,  "국제",       44000, "11톤트럭",  "주 3회",  "ACTIVE"),
    ("RTE017", "인천공항 국제선",        "HUB006", "HUB001", 45,  1.0,  "국제",        3500, "5톤트럭",   "일 1회",  "ACTIVE"),
    ("RTE018", "대구→경주 지선",         "HUB003", "HUB003", 65,  1.2,  "지선",        5000, "5톤트럭",   "주 3회",  "SEASONAL"),
    ("RTE019", "서울 퀵 라스트마일 C",   "HUB007", "HUB007", 10,  0.8,  "라스트마일",     0, "오토바이",  "탄력운행", "ACTIVE"),
    ("RTE020", "서울 퀵 라스트마일 D",   "HUB006", "HUB006", 8,   0.7,  "라스트마일",     0, "오토바이",  "탄력운행", "SUSPENDED"),
]

ROUTE_IDS = [r[0] for r in ROUTE_DEFS]

MST_ROUTE_FIELDS = [
    "ROUTE_ID", "ROUTE_NAME", "ORIGIN_HUB_ID", "DEST_HUB_ID",
    "DISTANCE_KM", "STANDARD_TIME_HOURS", "ROUTE_TYPE",
    "TOLL_KRW", "VEHICLE_TYPE_REQUIRED", "FREQUENCY", "STATUS",
]


def build_mst_route():
    rows = []
    for r in ROUTE_DEFS:
        rows.append(dict(zip(MST_ROUTE_FIELDS, r)))
    return rows


# ═══════════════════════════════════════════════════════════════
# lookups for FK joins
# ═══════════════════════════════════════════════════════════════

def build_lookups(vehicle_rows, route_rows):
    # vehicle_id -> (hub_id, cap_kg, cap_vol, driver_name)
    veh_map = {
        v["VEHICLE_ID"]: (
            v["HUB_ID"],
            float(v["CAPACITY_KG"]),
            float(v["CAPACITY_VOLUME_M3"]),
            v["DRIVER_NAME"],
            v["STATUS"],
        )
        for v in vehicle_rows
    }
    # route_id -> (origin_hub, dest_hub, distance_km, std_hours, route_type, toll)
    route_map = {
        r["ROUTE_ID"]: (
            r["ORIGIN_HUB_ID"],
            r["DEST_HUB_ID"],
            float(r["DISTANCE_KM"]),
            float(r["STANDARD_TIME_HOURS"]),
            r["ROUTE_TYPE"],
            float(r["TOLL_KRW"]),
            r["STATUS"],
        )
        for r in route_rows
    }
    # active vehicle ids
    active_veh_ids = [
        vid for vid, info in veh_map.items() if info[4] == "ACTIVE"
    ]
    # active route ids
    active_route_ids = [
        rid for rid, info in route_map.items() if info[6] == "ACTIVE"
    ]
    return veh_map, route_map, active_veh_ids, active_route_ids


# ═══════════════════════════════════════════════════════════════
# 4. FACT_DELIVERY
# ═══════════════════════════════════════════════════════════════

FAIL_REASONS = ["수취인부재", "주소불명", "배송불가지역", "반송요청"]

MST_DELIVERY_FIELDS = [
    "DELIVERY_ID", "VEHICLE_ID", "ROUTE_ID", "HUB_ID",
    "DELIVERY_DATE", "DEPARTURE_TIME", "ARRIVAL_TIME",
    "PACKAGE_COUNT", "TOTAL_WEIGHT_KG", "TOTAL_VOLUME_M3",
    "DELIVERY_SUCCESS_COUNT", "DELIVERY_FAIL_COUNT",
    "FAIL_REASON", "DRIVER_NAME", "STATUS",
]


def _season_factor(d: date) -> float:
    m = d.month
    wd = d.weekday()  # 0=Mon
    base = 1.0
    if m in (11, 12):
        base = random.uniform(1.5, 2.0)
    elif m in (2, 8):
        base = random.uniform(0.7, 0.8)
    if wd < 5:  # weekday
        base *= 1.3
    return base


def _departure_hour(route_type: str) -> int:
    if route_type == "간선":
        return random.randint(21, 23)
    elif route_type in ("지선",):
        return random.randint(6, 10)
    elif route_type == "라스트마일":
        return random.randint(9, 13)
    elif route_type == "국제":
        return random.randint(18, 22)
    return random.randint(6, 18)


def build_fact_delivery(vehicle_rows, route_rows, veh_map, route_map, active_veh_ids, active_route_ids):
    rows = []
    delivery_id_counter = 1
    start_date = date(2023, 1, 1)
    end_date = date(2024, 12, 31)
    delta = (end_date - start_date).days + 1

    # aim ~15000 records over 730 days → ~20/day, distribute via random
    for day_offset in range(delta):
        d = start_date + timedelta(days=day_offset)
        # number of deliveries for this day
        n_today = random.randint(15, 30)
        for _ in range(n_today):
            vid = random.choice(active_veh_ids)
            rid = random.choice(active_route_ids)
            hub_id, cap_kg, cap_vol, driver, _ = veh_map[vid]
            origin_hub, dest_hub, dist_km, std_hours, route_type, toll, _ = route_map[rid]

            sf = _season_factor(d)
            load_factor = random.uniform(0.60, 0.95)
            # base package count
            base_pkg = max(1, int(cap_kg / 15 * load_factor * sf))
            pkg_count = max(1, base_pkg)
            weight_kg = round(random.uniform(0.8, 1.2) * cap_kg * load_factor * sf, 1)
            weight_kg = min(weight_kg, cap_kg)
            vol_m3 = round(weight_kg / cap_kg * cap_vol * random.uniform(0.85, 1.05), 2)
            vol_m3 = min(vol_m3, cap_vol)

            # fail rate: normally 3-8%
            fail_rate = random.uniform(0.03, 0.08)
            if d.month in (11, 12):
                fail_rate = random.uniform(0.05, 0.12)
            fail_cnt = int(pkg_count * fail_rate)
            success_cnt = pkg_count - fail_cnt

            fail_reason = None
            if fail_cnt > 0:
                fail_reason = random.choice(FAIL_REASONS)

            dep_hour = _departure_hour(route_type)
            dep_min = random.randint(0, 59)
            dep_time = fmt_time(dep_hour, dep_min)

            # arrival time: NULL ~5%
            if random.random() < 0.05:
                arr_time = None
                status = "IN_TRANSIT"
            else:
                jitter = random.uniform(-0.3, 0.6)
                arr_hours = std_hours + jitter
                arr_total_min = dep_hour * 60 + dep_min + int(arr_hours * 60)
                arr_h = (arr_total_min // 60) % 24
                arr_m = arr_total_min % 60
                arr_time = fmt_time(arr_h, arr_m)
                if fail_cnt > 0 and success_cnt == 0:
                    status = "FAILED"
                elif fail_cnt > 0:
                    status = "PARTIAL"
                else:
                    status = "COMPLETED"

            rows.append({
                "DELIVERY_ID": f"DLV{delivery_id_counter:07d}",
                "VEHICLE_ID": vid,
                "ROUTE_ID": rid,
                "HUB_ID": origin_hub,
                "DELIVERY_DATE": fmt_date(d),
                "DEPARTURE_TIME": dep_time,
                "ARRIVAL_TIME": arr_time,
                "PACKAGE_COUNT": pkg_count,
                "TOTAL_WEIGHT_KG": weight_kg,
                "TOTAL_VOLUME_M3": vol_m3,
                "DELIVERY_SUCCESS_COUNT": success_cnt,
                "DELIVERY_FAIL_COUNT": fail_cnt,
                "FAIL_REASON": fail_reason,
                "DRIVER_NAME": driver,
                "STATUS": status,
            })
            delivery_id_counter += 1

    return rows


# ═══════════════════════════════════════════════════════════════
# 5. FACT_DELAY
# ═══════════════════════════════════════════════════════════════

DELAY_CAUSES = ["교통체증", "사고", "날씨", "설비고장", "인력부족", "집하지연", "수취인부재"]
SEVERITY_WEIGHTS = {
    "MINOR": 50,    # < 30 min
    "MODERATE": 35, # 30-120 min
    "SEVERE": 15,   # > 120 min
}

MST_DELAY_FIELDS = [
    "DELAY_ID", "DELIVERY_ID", "VEHICLE_ID", "ROUTE_ID",
    "DELAY_DATE", "SCHEDULED_ARRIVAL", "ACTUAL_ARRIVAL",
    "DELAY_MINUTES", "DELAY_CAUSE", "SEVERITY",
    "CUSTOMER_COMPLAINT", "COMPENSATION_KRW", "RESOLUTION_STATUS",
]


def _pick_severity():
    r = random.randint(1, 100)
    if r <= 50:
        return "MINOR"
    elif r <= 85:
        return "MODERATE"
    return "SEVERE"


def build_fact_delay(delivery_rows, route_map):
    """Pick ~20% of deliveries that have completed arrival and assign delay."""
    completed = [
        r for r in delivery_rows
        if r["ARRIVAL_TIME"] is not None and r["STATUS"] in ("COMPLETED", "PARTIAL", "FAILED")
    ]
    # sample ~20%
    n_delays = int(len(completed) * 0.20)
    sampled = random.sample(completed, min(n_delays, len(completed)))

    rows = []
    for i, dlv in enumerate(sampled):
        severity = _pick_severity()
        if severity == "MINOR":
            delay_min = random.randint(5, 29)
        elif severity == "MODERATE":
            delay_min = random.randint(30, 120)
        else:
            delay_min = random.randint(121, 360)

        # scheduled arrival from departure + std route hours
        rid = dlv["ROUTE_ID"]
        _, _, dist_km, std_hours, _, _, _ = route_map[rid]
        dep_time_str = dlv["DEPARTURE_TIME"]
        dep_h, dep_m = map(int, dep_time_str.split(":"))
        sched_total = dep_h * 60 + dep_m + int(std_hours * 60)
        sched_h = (sched_total // 60) % 24
        sched_m = sched_total % 60
        sched_arr = fmt_time(sched_h, sched_m)

        actual_total = sched_total + delay_min
        actual_h = (actual_total // 60) % 24
        actual_m = actual_total % 60

        # ~10% actual arrival NULL
        if random.random() < 0.10:
            actual_arr = None
        else:
            actual_arr = fmt_time(actual_h, actual_m)

        # peak delay probability
        delay_date = dlv["DELIVERY_DATE"]
        month = int(delay_date[5:7])

        cause_weights = [3, 2, 2, 1, 1, 2, 1]  # base
        if month in (11, 12):
            cause_weights[6] = 3  # 수취인부재 spike
            cause_weights[2] = 4  # 날씨
        elif month in (1, 2):
            cause_weights[2] = 4  # 날씨 (lunar new year / winter)
        total_w = sum(cause_weights)
        r_val = random.randint(1, total_w)
        cumul = 0
        cause = DELAY_CAUSES[0]
        for idx, w in enumerate(cause_weights):
            cumul += w
            if r_val <= cumul:
                cause = DELAY_CAUSES[idx]
                break

        # complaint: SEVERE → 80%, MODERATE → 40%, MINOR → 10%
        complaint_prob = {"MINOR": 0.10, "MODERATE": 0.40, "SEVERE": 0.80}[severity]
        complaint = "Y" if random.random() < complaint_prob else "N"

        # compensation: ~60% NULL overall; SEVERE always has if complaint
        if complaint == "Y":
            if severity == "SEVERE":
                comp = random.choice([3000, 5000, 10000, 15000, 20000])
            elif severity == "MODERATE":
                comp = maybe_null(random.choice([1000, 2000, 3000, 5000]), 0.40)
            else:
                comp = maybe_null(random.choice([1000, 2000]), 0.70)
        else:
            comp = None

        resolution_choices = (["RESOLVED"] * 7) + ["PENDING", "PENDING", "ESCALATED"]
        resolution = random.choice(resolution_choices)

        rows.append({
            "DELAY_ID": f"DLY{i + 1:06d}",
            "DELIVERY_ID": dlv["DELIVERY_ID"],
            "VEHICLE_ID": dlv["VEHICLE_ID"],
            "ROUTE_ID": dlv["ROUTE_ID"],
            "DELAY_DATE": delay_date,
            "SCHEDULED_ARRIVAL": sched_arr,
            "ACTUAL_ARRIVAL": actual_arr,
            "DELAY_MINUTES": delay_min,
            "DELAY_CAUSE": cause,
            "SEVERITY": severity,
            "CUSTOMER_COMPLAINT": complaint,
            "COMPENSATION_KRW": comp,
            "RESOLUTION_STATUS": resolution,
        })

    return rows


# ═══════════════════════════════════════════════════════════════
# 6. FACT_COST  (36 months × 25 vehicles)
# ═══════════════════════════════════════════════════════════════

# Monthly fuel prices (원/L) 2022-2024 rough trend
FUEL_PRICES = {}
base_price = {"경유": 1550, "LNG": 900, "전기": 180}

for yr in range(2022, 2025):
    for mo in range(1, 13):
        key = f"{yr}-{mo:02d}"
        # slight monthly variation
        FUEL_PRICES[key] = {
            "경유": int(base_price["경유"] * random.uniform(0.90, 1.20)),
            "LNG":  int(base_price["LNG"] * random.uniform(0.88, 1.15)),
            "전기": int(base_price["전기"] * random.uniform(0.95, 1.05)),
        }

MST_COST_FIELDS = [
    "COST_ID", "VEHICLE_ID", "ROUTE_ID", "YEAR_MONTH",
    "FUEL_COST_KRW", "TOLL_COST_KRW", "MAINTENANCE_COST_KRW",
    "DRIVER_WAGE_KRW", "INSURANCE_KRW", "DEPRECIATION_KRW",
    "OTHER_COST_KRW", "TOTAL_COST_KRW",
    "REVENUE_KRW", "PROFIT_KRW", "COST_PER_KM_KRW",
]


def build_fact_cost(vehicle_rows, route_rows, veh_map, route_map):
    rows = []
    cost_id = 1

    # purchase_year per vehicle for age-based maintenance
    purchase_year_map = {v["VEHICLE_ID"]: int(v["PURCHASE_DATE"][:4]) for v in vehicle_rows}

    for yr in range(2022, 2025):
        for mo in range(1, 13):
            ym = f"{yr}-{mo:02d}"
            fp = FUEL_PRICES[ym]

            for v in vehicle_rows:
                vid = v["VEHICLE_ID"]
                fuel_type = v["FUEL_TYPE"]
                efficiency = float(v["FUEL_EFFICIENCY_KM_PER_L"])
                cap_kg = float(v["CAPACITY_KG"])

                # estimated monthly distance
                if v["VEHICLE_TYPE"] in ("오토바이", "전기밴"):
                    monthly_km = random.uniform(1500, 4000)
                elif v["VEHICLE_TYPE"] in ("11톤트럭",):
                    monthly_km = random.uniform(8000, 22000)
                elif v["VEHICLE_TYPE"] in ("5톤트럭", "냉동차"):
                    monthly_km = random.uniform(5000, 15000)
                else:  # 1톤트럭
                    monthly_km = random.uniform(3000, 9000)

                # peak season: more distance
                if mo in (11, 12):
                    monthly_km *= random.uniform(1.3, 1.6)
                elif mo in (2, 8):
                    monthly_km *= random.uniform(0.7, 0.9)

                monthly_km = round(monthly_km, 0)

                # fuel cost
                fuel_per_unit = fp[fuel_type]
                fuel_cost = int(monthly_km / efficiency * fuel_per_unit)

                # toll cost
                avg_toll_per_km = 90 if fuel_type != "오토바이" else 0
                toll_cost = int(monthly_km * random.uniform(0.05, 0.25) * avg_toll_per_km)

                # maintenance: older vehicle → higher; NULL 40%
                vehicle_age = yr - purchase_year_map[vid]
                base_maint = 80000 + vehicle_age * 15000
                maint_spike = random.random() < 0.15  # 15% chance of major maintenance
                if maint_spike:
                    maint_cost = int(base_maint * random.uniform(3, 8))
                else:
                    maint_cost = int(base_maint * random.uniform(0.5, 1.5))
                maintenance_cost = maybe_null(maint_cost, 0.40)

                # driver wage (monthly, includes overtime for peak)
                base_wage = 2800000
                if mo in (11, 12):
                    driver_wage = int(base_wage * random.uniform(1.2, 1.4))
                else:
                    driver_wage = int(base_wage * random.uniform(0.95, 1.10))

                # insurance (annual / 12)
                insurance_annual = {
                    "11톤트럭": 4200000,
                    "5톤트럭":  2800000,
                    "냉동차":   3100000,
                    "1톤트럭":  1800000,
                    "오토바이": 600000,
                    "전기밴":   1400000,
                }.get(v["VEHICLE_TYPE"], 2000000)
                insurance = int(insurance_annual / 12 * random.uniform(0.95, 1.05))

                # depreciation (straight line ~7 years)
                purchase_price = {
                    "11톤트럭": 120000000,
                    "5톤트럭":  70000000,
                    "냉동차":   85000000,
                    "1톤트럭":  30000000,
                    "오토바이": 6000000,
                    "전기밴":   45000000,
                }.get(v["VEHICLE_TYPE"], 50000000)
                depreciation = int(purchase_price / (7 * 12))

                # other cost: NULL 25%
                other_cost = maybe_null(int(random.uniform(50000, 300000)), 0.25)

                # total
                maint_val = maintenance_cost if maintenance_cost is not None else 0
                other_val = other_cost if other_cost is not None else 0
                total_cost = fuel_cost + toll_cost + maint_val + driver_wage + insurance + depreciation + other_val

                # revenue: package count × avg revenue
                avg_rev_per_pkg = random.uniform(3500, 6500)
                estimated_pkg = int(monthly_km / 50 * cap_kg / 5000 * 100)
                estimated_pkg = max(50, estimated_pkg)
                if mo in (11, 12):
                    estimated_pkg = int(estimated_pkg * random.uniform(1.4, 1.8))
                revenue = int(estimated_pkg * avg_rev_per_pkg)

                profit = revenue - total_cost

                # cost per km: NULL 15%
                cpkm = maybe_null(round(total_cost / monthly_km, 1) if monthly_km > 0 else None, 0.15)

                # route_id: NULL ~30%
                route_id = maybe_null(random.choice(ROUTE_IDS), 0.30)

                rows.append({
                    "COST_ID": f"CST{cost_id:07d}",
                    "VEHICLE_ID": vid,
                    "ROUTE_ID": route_id,
                    "YEAR_MONTH": ym,
                    "FUEL_COST_KRW": fuel_cost,
                    "TOLL_COST_KRW": toll_cost,
                    "MAINTENANCE_COST_KRW": maintenance_cost,
                    "DRIVER_WAGE_KRW": driver_wage,
                    "INSURANCE_KRW": insurance,
                    "DEPRECIATION_KRW": depreciation,
                    "OTHER_COST_KRW": other_cost,
                    "TOTAL_COST_KRW": total_cost,
                    "REVENUE_KRW": revenue,
                    "PROFIT_KRW": profit,
                    "COST_PER_KM_KRW": cpkm,
                })
                cost_id += 1

    return rows


# ═══════════════════════════════════════════════════════════════
# SCHEMA
# ═══════════════════════════════════════════════════════════════

SCHEMA = {
    "domain": "logistics",
    "description": "물류·배송 운영 관리 데모 데이터셋",
    "tables": {
        "MST_HUB": {
            "description": "물류 허브(거점) 마스터",
            "primary_key": "HUB_ID",
            "columns": {
                "HUB_ID": {"type": "VARCHAR(6)", "description": "허브 고유 ID (HUBxxx)"},
                "HUB_NAME": {"type": "VARCHAR(50)", "description": "허브명"},
                "HUB_TYPE": {"type": "VARCHAR(10)", "description": "허브 유형: 메가허브/지역허브/서브허브/픽업포인트"},
                "REGION": {"type": "VARCHAR(10)", "description": "소재 광역 행정구역"},
                "ADDRESS": {"type": "VARCHAR(100)", "description": "도로명 주소"},
                "CAPACITY_PACKAGES_DAILY": {"type": "INTEGER", "description": "일일 최대 처리 패키지 수"},
                "DOCK_COUNT": {"type": "INTEGER", "description": "하역 도크 수"},
                "OPERATING_HOURS": {"type": "VARCHAR(15)", "description": "운영 시간 (HH:MM-HH:MM)"},
                "MANAGER_NAME": {"type": "VARCHAR(20)", "description": "허브 관리자 이름"},
                "STATUS": {"type": "VARCHAR(10)", "description": "운영 상태: ACTIVE/EXPANSION/INACTIVE"},
            },
        },
        "MST_VEHICLE": {
            "description": "배송 차량 마스터",
            "primary_key": "VEHICLE_ID",
            "foreign_keys": {"HUB_ID": "MST_HUB.HUB_ID"},
            "columns": {
                "VEHICLE_ID": {"type": "VARCHAR(6)", "description": "차량 고유 ID (VHCxxx)"},
                "VEHICLE_NAME": {"type": "VARCHAR(30)", "description": "차량 이름"},
                "VEHICLE_TYPE": {"type": "VARCHAR(10)", "description": "차량 유형: 5톤트럭/11톤트럭/1톤트럭/냉동차/오토바이/전기밴"},
                "LICENSE_PLATE": {"type": "VARCHAR(15)", "description": "차량 번호판"},
                "HUB_ID": {"type": "VARCHAR(6)", "description": "소속 허브 FK"},
                "CAPACITY_KG": {"type": "DECIMAL(8,1)", "description": "최대 적재 중량 (kg)"},
                "CAPACITY_VOLUME_M3": {"type": "DECIMAL(6,2)", "description": "최대 적재 부피 (m³)"},
                "FUEL_TYPE": {"type": "VARCHAR(5)", "description": "연료 유형: 경유/LNG/전기"},
                "FUEL_EFFICIENCY_KM_PER_L": {"type": "DECIMAL(5,1)", "description": "연비 (km/L 또는 km/kWh)"},
                "DRIVER_NAME": {"type": "VARCHAR(20)", "description": "전담 기사 이름"},
                "STATUS": {"type": "VARCHAR(15)", "description": "차량 상태: ACTIVE/MAINTENANCE/RETIRED"},
                "PURCHASE_DATE": {"type": "DATE", "description": "구매일"},
                "MILEAGE_KM": {"type": "INTEGER", "description": "누적 주행 거리 (km)"},
            },
        },
        "MST_ROUTE": {
            "description": "배송 노선 마스터",
            "primary_key": "ROUTE_ID",
            "foreign_keys": {
                "ORIGIN_HUB_ID": "MST_HUB.HUB_ID",
                "DEST_HUB_ID": "MST_HUB.HUB_ID",
            },
            "columns": {
                "ROUTE_ID": {"type": "VARCHAR(6)", "description": "노선 고유 ID (RTExxx)"},
                "ROUTE_NAME": {"type": "VARCHAR(50)", "description": "노선명"},
                "ORIGIN_HUB_ID": {"type": "VARCHAR(6)", "description": "출발 허브 FK"},
                "DEST_HUB_ID": {"type": "VARCHAR(6)", "description": "도착 허브 FK"},
                "DISTANCE_KM": {"type": "DECIMAL(6,1)", "description": "노선 거리 (km)"},
                "STANDARD_TIME_HOURS": {"type": "DECIMAL(4,1)", "description": "표준 소요 시간 (시간)"},
                "ROUTE_TYPE": {"type": "VARCHAR(10)", "description": "노선 유형: 간선/지선/라스트마일/국제"},
                "TOLL_KRW": {"type": "INTEGER", "description": "편도 통행료 (원)"},
                "VEHICLE_TYPE_REQUIRED": {"type": "VARCHAR(10)", "description": "필요 차량 유형"},
                "FREQUENCY": {"type": "VARCHAR(10)", "description": "운행 빈도"},
                "STATUS": {"type": "VARCHAR(10)", "description": "노선 상태: ACTIVE/SUSPENDED/SEASONAL"},
            },
        },
        "FACT_DELIVERY": {
            "description": "배송 실적 팩트 (2023-2024, ~15,000건)",
            "primary_key": "DELIVERY_ID",
            "foreign_keys": {
                "VEHICLE_ID": "MST_VEHICLE.VEHICLE_ID",
                "ROUTE_ID": "MST_ROUTE.ROUTE_ID",
                "HUB_ID": "MST_HUB.HUB_ID",
            },
            "columns": {
                "DELIVERY_ID": {"type": "VARCHAR(10)", "description": "배송 고유 ID (DLVxxxxxxx)"},
                "VEHICLE_ID": {"type": "VARCHAR(6)", "description": "차량 ID FK"},
                "ROUTE_ID": {"type": "VARCHAR(6)", "description": "노선 ID FK"},
                "HUB_ID": {"type": "VARCHAR(6)", "description": "출발 허브 ID FK"},
                "DELIVERY_DATE": {"type": "DATE", "description": "배송일"},
                "DEPARTURE_TIME": {"type": "VARCHAR(5)", "description": "출발 시각 (HH:MM)"},
                "ARRIVAL_TIME": {"type": "VARCHAR(5)", "nullable": True, "description": "도착 시각 (HH:MM); NULL이면 운행 중"},
                "PACKAGE_COUNT": {"type": "INTEGER", "description": "배송 패키지 수"},
                "TOTAL_WEIGHT_KG": {"type": "DECIMAL(8,1)", "description": "총 배송 중량 (kg)"},
                "TOTAL_VOLUME_M3": {"type": "DECIMAL(6,2)", "description": "총 배송 부피 (m³)"},
                "DELIVERY_SUCCESS_COUNT": {"type": "INTEGER", "description": "성공 건수"},
                "DELIVERY_FAIL_COUNT": {"type": "INTEGER", "description": "실패 건수"},
                "FAIL_REASON": {"type": "VARCHAR(15)", "nullable": True, "description": "실패 사유: 수취인부재/주소불명/배송불가지역/반송요청"},
                "DRIVER_NAME": {"type": "VARCHAR(20)", "description": "기사 이름"},
                "STATUS": {"type": "VARCHAR(10)", "description": "상태: COMPLETED/IN_TRANSIT/FAILED/PARTIAL"},
            },
        },
        "FACT_DELAY": {
            "description": "배송 지연 이벤트 팩트 (2023-2024, ~3,000건)",
            "primary_key": "DELAY_ID",
            "foreign_keys": {
                "DELIVERY_ID": "FACT_DELIVERY.DELIVERY_ID",
                "VEHICLE_ID": "MST_VEHICLE.VEHICLE_ID",
                "ROUTE_ID": "MST_ROUTE.ROUTE_ID",
            },
            "columns": {
                "DELAY_ID": {"type": "VARCHAR(9)", "description": "지연 고유 ID (DLYxxxxxx)"},
                "DELIVERY_ID": {"type": "VARCHAR(10)", "description": "배송 ID FK"},
                "VEHICLE_ID": {"type": "VARCHAR(6)", "description": "차량 ID FK"},
                "ROUTE_ID": {"type": "VARCHAR(6)", "description": "노선 ID FK"},
                "DELAY_DATE": {"type": "DATE", "description": "지연 발생일"},
                "SCHEDULED_ARRIVAL": {"type": "VARCHAR(5)", "description": "예정 도착 시각"},
                "ACTUAL_ARRIVAL": {"type": "VARCHAR(5)", "nullable": True, "description": "실제 도착 시각; NULL이면 미도착"},
                "DELAY_MINUTES": {"type": "INTEGER", "description": "지연 시간 (분)"},
                "DELAY_CAUSE": {"type": "VARCHAR(10)", "description": "지연 원인"},
                "SEVERITY": {"type": "VARCHAR(10)", "description": "지연 등급: MINOR/MODERATE/SEVERE"},
                "CUSTOMER_COMPLAINT": {"type": "CHAR(1)", "description": "고객 불만 여부: Y/N"},
                "COMPENSATION_KRW": {"type": "INTEGER", "nullable": True, "description": "보상금 (원); NULL이면 보상 없음"},
                "RESOLUTION_STATUS": {"type": "VARCHAR(10)", "description": "처리 상태: RESOLVED/PENDING/ESCALATED"},
            },
        },
        "FACT_COST": {
            "description": "월별 차량 비용 팩트 (2022-2024, 36개월 × 25대)",
            "primary_key": "COST_ID",
            "foreign_keys": {
                "VEHICLE_ID": "MST_VEHICLE.VEHICLE_ID",
                "ROUTE_ID": "MST_ROUTE.ROUTE_ID",
            },
            "columns": {
                "COST_ID": {"type": "VARCHAR(10)", "description": "비용 고유 ID (CSTxxxxxxx)"},
                "VEHICLE_ID": {"type": "VARCHAR(6)", "description": "차량 ID FK"},
                "ROUTE_ID": {"type": "VARCHAR(6)", "nullable": True, "description": "노선 ID FK; NULL이면 월간 합산"},
                "YEAR_MONTH": {"type": "VARCHAR(7)", "description": "연월 (YYYY-MM)"},
                "FUEL_COST_KRW": {"type": "INTEGER", "description": "연료비 (원)"},
                "TOLL_COST_KRW": {"type": "INTEGER", "description": "통행료 (원)"},
                "MAINTENANCE_COST_KRW": {"type": "INTEGER", "nullable": True, "description": "정비비 (원); NULL이면 정비 없음"},
                "DRIVER_WAGE_KRW": {"type": "INTEGER", "description": "기사 인건비 (원)"},
                "INSURANCE_KRW": {"type": "INTEGER", "description": "보험료 (원)"},
                "DEPRECIATION_KRW": {"type": "INTEGER", "description": "감가상각비 (원)"},
                "OTHER_COST_KRW": {"type": "INTEGER", "nullable": True, "description": "기타 비용 (원); NULL 약 25%"},
                "TOTAL_COST_KRW": {"type": "INTEGER", "description": "총 비용 (원)"},
                "REVENUE_KRW": {"type": "INTEGER", "description": "매출 (원)"},
                "PROFIT_KRW": {"type": "INTEGER", "description": "영업이익 (원)"},
                "COST_PER_KM_KRW": {"type": "DECIMAL(8,1)", "nullable": True, "description": "km당 비용 (원); NULL 약 15%"},
            },
        },
    },
}


# ═══════════════════════════════════════════════════════════════
# LOGIC DOCUMENT
# ═══════════════════════════════════════════════════════════════

LOGIC_DOC = """================================================================
물류·배송 운영 관리 전략 문서
작성 기준: 2025년 물류 운영 정책
================================================================

1. 배송 네트워크 설계 원칙
   Hub & Spoke 모델:
   - 메가허브: 간선 집결, 대형 차량 운용
   - 지역허브: 지선 분류, 라스트마일 출발
   - 서브허브: 도심 마지막 거점

   간선: 허브-허브 야간 운행 (22:00~06:00)
   지선: 허브-서브허브 오전 운행 (06:00~12:00)
   라스트마일: 서브허브-고객 오후 배송 (12:00~21:00)

2. 차량 효율화 (적재율 관리)
   목표 적재율: 85% 이상 (kg 기준)
   - 적재율 < 60%: 공동 배송 검토, 루트 통합
   - 적재율 > 95%: 추가 차량 투입

   연비 관리 (공차율 최소화):
   - 왕복 구간 적재 비율: 70% 이상 목표
   - 공차 운행 경고: 50km 이상 공차 시 알림

3. 배송 지연 관리 기준
   SLA (서비스 수준 협약):
   - 익일 배송: 접수 다음날 18시까지 (당일 23시 마감)
   - 당일 배송: 접수 후 4시간 이내
   - 새벽 배송: 익일 07시까지

   지연 등급별 대응:
   - MINOR (30분 미만): 시스템 기록만
   - MODERATE (30~120분): 고객 SMS 발송, 사유 기록
   - SEVERE (120분 초과): 고객 전화 + 쿠폰 보상 검토

   지연 원인별 예방책:
   - 교통체증: 피크타임 우회 루트 사전 설정
   - 날씨: 기상 예보 연동 사전 대기 차량 배치
   - 수취인 부재: 사전 배송 예정 알림 발송

4. 비용 구조 및 단가 분석
   차량 유형별 손익분기 활용률:
   - 5톤 트럭: 월 12,000km 이상 운행 시 수익
   - 11톤 트럭: 월 18,000km 이상
   - 라스트마일(1톤): 일 40건 이상 배송 시 수익

   비용 절감 레버:
   - 연료비: 군집 주행, LNG/전기차 전환
   - 인건비: 배송 밀도 최적화
   - 톨: 통행료 최적 루트 알고리즘

5. 피크 시즌 대응 (11~12월)
   - 임시 차량 외주: 필요량의 30% 사전 계약
   - 허브 야간 연장 운영 (24시간)
   - 비상 인력 풀 사전 확보
   - 고객 배송 예정일 조정 커뮤니케이션

6. KPI 정의
   - 배송 성공률: 98% 이상
   - 정시 배송률: 95% 이상 (SLA 기준)
   - 적재율: 85% 이상
   - 고객 불만 건수: 배송 1,000건당 5건 이하
   - 차량 가동률: 90% 이상
   - km당 비용: 전년 대비 3% 이상 절감
"""


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"\n[logistics] generating data → {DATA_DIR}\n")

    # --- Master tables ---
    hub_rows = build_mst_hub()
    write_csv("MST_HUB.csv", MST_HUB_FIELDS, hub_rows)

    vehicle_rows, veh_spec_list = build_mst_vehicle()
    write_csv("MST_VEHICLE.csv", MST_VEHICLE_FIELDS, vehicle_rows)

    route_rows = build_mst_route()
    write_csv("MST_ROUTE.csv", MST_ROUTE_FIELDS, route_rows)

    # --- Build lookup dicts ---
    veh_map, route_map, active_veh_ids, active_route_ids = build_lookups(vehicle_rows, route_rows)

    # --- Fact tables ---
    delivery_rows = build_fact_delivery(vehicle_rows, route_rows, veh_map, route_map, active_veh_ids, active_route_ids)
    write_csv("FACT_DELIVERY.csv", MST_DELIVERY_FIELDS, delivery_rows)

    delay_rows = build_fact_delay(delivery_rows, route_map)
    write_csv("FACT_DELAY.csv", MST_DELAY_FIELDS, delay_rows)

    cost_rows = build_fact_cost(vehicle_rows, route_rows, veh_map, route_map)
    write_csv("FACT_COST.csv", MST_COST_FIELDS, cost_rows)

    # --- Schema JSON ---
    schema_path = os.path.join(DATA_DIR, "SCHEMA_DEFINITION.json")
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(SCHEMA, f, ensure_ascii=False, indent=2)
    print(f"  wrote schema  → SCHEMA_DEFINITION.json")

    # --- Logic document ---
    logic_path = os.path.join(DATA_DIR, "LOGIC_DOCUMENT.txt")
    with open(logic_path, "w", encoding="utf-8") as f:
        f.write(LOGIC_DOC)
    print(f"  wrote logic   → LOGIC_DOCUMENT.txt")

    print(f"\n[done] {len(hub_rows)} hubs | {len(vehicle_rows)} vehicles | {len(route_rows)} routes")
    print(f"       {len(delivery_rows):,} deliveries | {len(delay_rows):,} delays | {len(cost_rows):,} cost records")
