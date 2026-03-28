"""범용 비즈니스 도메인 프리셋 (기본값)"""

PRESET = {
    "entity_types": {
        "person":       "#2196F3",
        "organization": "#9C27B0",
        "process":      "#FF9800",
        "resource":     "#00BCD4",
        "issue":        "#F44336",
        "decision":     "#4CAF50",
        "metric":       "#607D8B",
        "default":      "#9E9E9E",
    },
    "terminology": [
        "전략", "목표", "성과", "리스크", "의사결정",
        "KPI", "예산", "로드맵", "이해관계자", "우선순위",
    ],
    "document_patterns": ["회의록", "보고서", "기획서", "정책문서"],
    "analysis_focus":    ["핵심 의사결정", "리스크 관리", "성과 측정", "실행 과제"],
    "theme_color":       "#2563EB",
    "app_icon":          "🤖",
}
