"""물류·배송 도메인 프리셋"""

PRESET = {
    "entity_types": {
        "person":   "#2196F3",
        "location": "#4CAF50",
        "process":  "#FF9800",
        "resource": "#00BCD4",
        "issue":    "#F44336",
        "decision": "#795548",
        "metric":   "#607D8B",
        "default":  "#9E9E9E",
    },
    "terminology": [
        "배송", "재고", "창고", "운송비", "적재율", "납기",
        "반품", "라스트마일", "허브", "루트최적화",
        "SLA", "트래킹", "온타임", "포워딩",
    ],
    "document_patterns": ["배송보고서", "재고현황", "운영회의록", "비용분석"],
    "analysis_focus":    ["배송 효율", "재고 관리", "비용 최적화", "고객 서비스"],
    "theme_color":       "#0284c7",
    "app_icon":          "🚚",
}
