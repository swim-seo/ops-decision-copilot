"""뷰티·이커머스 도메인 프리셋"""

PRESET = {
    "entity_types": {
        "person":   "#2196F3",
        "product":  "#E91E63",
        "supplier": "#9C27B0",
        "process":  "#FF9800",
        "issue":    "#F44336",
        "decision": "#4CAF50",
        "metric":   "#607D8B",
        "default":  "#9E9E9E",
    },
    "terminology": [
        "SKU", "OEM", "ODM", "성분", "포뮬레이션", "충전량",
        "용기", "안전성시험", "CPNP", "리드타임", "MOQ",
        "단종", "시즌", "채널", "D2C",
    ],
    "document_patterns": ["회의록", "품질보고서", "원가분석", "VOC리포트"],
    "analysis_focus":    ["제품 품질", "원가 관리", "공급망 리스크", "고객 만족"],
    "theme_color":       "#E91E63",
    "app_icon":          "💄",
}
