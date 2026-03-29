"""
CSV → KnowledgeGraph 엣지 생성 검증 테스트

대상: orders, products, customers 3개 테이블
확인 항목:
  1. extract_csv_schema — FK 후보 컬럼 감지 정확성
  2. build_from_csv_schema 1st pass — 노드만 생성, 엣지 없음
  3. build_from_csv_schema 2nd pass — FK 엣지 자동 생성
  4. query_by_id — 연결 노드·엣지 반환
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from modules.document_parser import extract_csv_schema
from modules.knowledge_graph import KnowledgeGraph

# ── 테스트 CSV 데이터 ────────────────────────────────────────────────────────
CSV_ORDERS = """\
order_id,product_id,customer_no,amount,order_date
1,P001,C100,50000,2024-01-01
2,P002,C101,30000,2024-01-02
3,P001,C100,20000,2024-01-03
"""

CSV_PRODUCTS = """\
product_id,product_name,category_no,price,stock
P001,상품A,CAT1,10000,100
P002,상품B,CAT2,15000,200
"""

CSV_CUSTOMERS = """\
customer_no,customer_name,region_id,grade
C100,홍길동,R1,VIP
C101,김철수,R2,일반
"""

CSVS = [
    ("orders.csv",    CSV_ORDERS),
    ("products.csv",  CSV_PRODUCTS),
    ("customers.csv", CSV_CUSTOMERS),
]

PASS = "[PASS]"
FAIL = "[FAIL]"


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = PASS if condition else FAIL
    print(f"  {status}  {label}" + (f" — {detail}" if detail else ""))
    return condition


# ════════════════════════════════════════════════════════════════════════════
# STEP 1. extract_csv_schema — FK 후보 감지
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("STEP 1. extract_csv_schema FK 후보 감지")
print("="*60)

schemas = {}
all_ok = True

EXPECTED_FK = {
    "orders":    {"product_id", "customer_no"},   # order_id는 자기 테이블 PK → self-ref 필터 대상
    "products":  {"product_id", "category_no"},
    "customers": {"customer_no", "region_id"},
}

for fname, raw in CSVS:
    schema = extract_csv_schema(fname, raw)
    schemas[schema["table_name"]] = schema
    fk_set = set(schema["fk_candidates"])
    expected = EXPECTED_FK[schema["table_name"]]

    print(f"\n  [{fname}]")
    print(f"    컬럼     : {schema['columns']}")
    print(f"    FK후보   : {schema['fk_candidates']}")
    print(f"    col_types: {schema['col_types']}")

    for col in expected:
        ok = col in fk_set
        all_ok &= check(f"FK 감지: {col}", ok)

print()
check("STEP1 전체", all_ok)


# ════════════════════════════════════════════════════════════════════════════
# STEP 2. 1st pass — 노드만 생성, 엣지 없어야 함
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("STEP 2. 1st pass — 노드 생성, 엣지 0개 확인")
print("="*60)

kg = KnowledgeGraph()
for name, schema in schemas.items():
    kg.build_from_csv_schema(schema, [])   # all_table_names=[] → FK 해석 불가

nodes_after_1st = list(kg.graph.nodes)
edges_after_1st = list(kg.graph.edges)

print(f"\n  노드: {nodes_after_1st}")
print(f"  엣지: {edges_after_1st}")

check("노드 3개 생성", len(nodes_after_1st) == 3, str(nodes_after_1st))
check("1st pass 엣지 0개", len(edges_after_1st) == 0, str(edges_after_1st))


# ════════════════════════════════════════════════════════════════════════════
# STEP 3. 2nd pass — FK 엣지 생성 확인
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("STEP 3. 2nd pass — FK 엣지 생성 확인")
print("="*60)

all_known_tables = list(kg.graph.nodes)  # ['orders', 'products', 'customers']
print(f"\n  all_known_tables = {all_known_tables}")

for name, schema in schemas.items():
    kg.build_from_csv_schema(schema, all_known_tables)

edges = [(u, d["relation"], v) for u, v, d in kg.graph.edges(data=True)]
print(f"\n  생성된 엣지:")
for e in edges:
    print(f"    {e[0]}  --[{e[1]}]-->  {e[2]}")

# 기대 엣지 (orders가 products/customers를 참조, 자기 참조 제외)
EXPECTED_EDGES = {
    ("orders", "products"),    # product_id FK
    ("orders", "customers"),   # customer_no FK
}

all_ok = True
for src, tgt in EXPECTED_EDGES:
    exists = any(u == src and v == tgt for u, v, _ in kg.graph.edges(data=True))
    all_ok &= check(f"엣지 존재: {src} → {tgt}", exists)

# 자기 참조 엣지가 없어야 함
self_edges = [(u, v) for u, v in kg.graph.edges() if u == v]
all_ok &= check("자기 참조 엣지 없음", len(self_edges) == 0, str(self_edges))

print()
check("STEP3 전체", all_ok)


# ════════════════════════════════════════════════════════════════════════════
# STEP 4. FK 매칭 로직 상세 추적 (실패 시 원인 파악용)
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("STEP 4. FK 매칭 로직 상세 추적")
print("="*60)

_FK_SUFFIXES = ("_id", "_no", "_code", "_num", "_key", "_seq", "_pk", "번호", "코드")

all_names_map = {n.lower(): n for n in all_known_tables}
print(f"\n  all_names_map = {all_names_map}")

for table_name, schema in schemas.items():
    print(f"\n  [{table_name}] FK 후보: {schema['fk_candidates']}")
    for fk_col in schema["fk_candidates"]:
        for suffix in _FK_SUFFIXES:
            if fk_col.lower().endswith(suffix):
                ref_candidate = fk_col[: -len(suffix)].lower()
                print(f"    '{fk_col}' → suffix='{suffix}' → ref_candidate='{ref_candidate}'")

                matched_ref = None
                if ref_candidate in all_names_map:
                    matched_ref = all_names_map[ref_candidate]
                    print(f"      정확 매칭: '{ref_candidate}' → '{matched_ref}'")
                elif ref_candidate + "s" in all_names_map:
                    matched_ref = all_names_map[ref_candidate + "s"]
                    print(f"      복수형 매칭: '{ref_candidate}s' → '{matched_ref}'")
                else:
                    for tname_lower, tname in all_names_map.items():
                        if tname_lower.startswith(ref_candidate) or ref_candidate.startswith(tname_lower):
                            matched_ref = tname
                            print(f"      접두 매칭: '{ref_candidate}' ~ '{tname_lower}' → '{matched_ref}'")
                            break
                    if matched_ref is None:
                        print(f"      ❌ 매칭 실패: '{ref_candidate}'와 일치하는 테이블 없음")

                if matched_ref:
                    if matched_ref == table_name:
                        print(f"      ⏭  자기 참조 → 스킵")
                    else:
                        print(f"      → 엣지 추가: {table_name} --[{fk_col}]--> {matched_ref}")
                break


# ════════════════════════════════════════════════════════════════════════════
# STEP 5. query_by_id
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("STEP 5. query_by_id 연결 노드 반환")
print("="*60)

for query in ["product", "order", "customer"]:
    result = kg.query_by_id(query)
    matched_ids = [n["id"] for n in result["matched_nodes"]]
    connected_ids = [n["id"] for n in result["connected_nodes"]]
    edge_strs = [f"{e['from']}→{e['to']}({e['relation']})" for e in result["edges"]]
    print(f"\n  query='{query}'")
    print(f"    matched  : {matched_ids}")
    print(f"    connected: {connected_ids}")
    print(f"    edges    : {edge_strs}")


# ════════════════════════════════════════════════════════════════════════════
# 최종 요약
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
stats = kg.get_stats()
print(f"최종 KG 상태: 노드 {stats['nodes']}개, 엣지 {stats['edges']}개")
print(f"엣지 목록: {[(u,v) for u,v in kg.graph.edges()]}")
print("="*60 + "\n")
