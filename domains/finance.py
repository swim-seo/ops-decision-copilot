"""금융·투자 도메인 프리셋"""

PRESET = {
    "entity_types": {
        "person":       "#2196F3",
        "organization": "#9C27B0",
        "product":      "#795548",
        "process":      "#FF9800",
        "issue":        "#F44336",
        "decision":     "#4CAF50",
        "metric":       "#607D8B",
        "default":      "#9E9E9E",
    },
    "terminology": [
        "포트폴리오", "리스크", "수익률", "규제준수", "AUM",
        "신용등급", "유동성", "헤지", "바젤", "IFRS",
        "VaR", "스트레스테스트", "NAV", "Alpha", "Beta",
    ],
    "document_patterns": ["투자보고서", "리스크보고서", "이사회회의록", "실적보고"],
    "analysis_focus":    ["리스크 관리", "수익 극대화", "규제 준수", "운영 효율"],
    "theme_color":       "#4CAF50",
    "app_icon":          "💰",
}
