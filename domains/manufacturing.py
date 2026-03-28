"""제조·생산 도메인 프리셋"""

PRESET = {
    "entity_types": {
        "person":   "#2196F3",
        "product":  "#795548",
        "process":  "#FF9800",
        "resource": "#00BCD4",
        "issue":    "#F44336",
        "decision": "#4CAF50",
        "metric":   "#607D8B",
        "default":  "#9E9E9E",
    },
    "terminology": [
        "생산계획", "불량률", "공정개선", "납기", "재고",
        "설비가동률", "OEE", "Takt Time", "BOM", "WIP",
        "6시그마", "Lean", "Kaizen", "품질관리", "로트",
    ],
    "document_patterns": ["생산일보", "품질보고서", "불량분석보고서"],
    "analysis_focus":    ["생산 효율", "품질 관리", "설비 유지보수", "원가 절감"],
    "theme_color":       "#607D8B",
    "app_icon":          "🏭",
}
