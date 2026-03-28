"""에너지 도메인 프리셋"""

PRESET = {
    "entity_types": {
        "person":   "#2196F3",
        "facility": "#FF9800",
        "resource": "#00BCD4",
        "process":  "#795548",
        "issue":    "#F44336",
        "decision": "#4CAF50",
        "metric":   "#607D8B",
        "default":  "#9E9E9E",
    },
    "terminology": [
        "발전량", "수요예측", "그리드", "ESS", "탄소중립",
        "PPA", "설비이용률", "RE100", "GHG", "계통연계",
        "REC", "발전단가", "부하율", "피크전력",
    ],
    "document_patterns": ["운영보고서", "설비점검보고서", "안전보고서"],
    "analysis_focus":    ["에너지 효율", "설비 안전", "비용 최적화", "환경 규제"],
    "theme_color":       "#FF9800",
    "app_icon":          "⚡",
}
