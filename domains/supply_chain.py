"""공급망·재고 관리 도메인 프리셋"""

PRESET = {
    "entity_types": {
        "person":   "#2196F3",
        "supplier": "#9C27B0",
        "product":  "#795548",
        "location": "#4CAF50",
        "issue":    "#F44336",
        "decision": "#2563EB",
        "metric":   "#607D8B",
        "default":  "#9E9E9E",
    },
    "terminology": [
        "리드타임", "재고", "발주", "공급업체", "SKU", "창고",
        "납기", "안전재고", "COVERAGE", "MOQ", "발주점",
        "재보충", "인바운드", "아웃바운드", "3PL",
    ],
    "document_patterns": ["발주서", "재고현황", "공급망보고서", "납기분석"],
    "analysis_focus":    ["재고 최적화", "납기 준수", "공급업체 관리", "수요 예측"],
    "theme_color":       "#2563EB",
    "app_icon":          "📦",
}
