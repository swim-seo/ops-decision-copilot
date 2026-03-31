#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
도메인 자동 인식 정확도 평가 — 분류 Accuracy
테스트셋: eval/domain_testset.json (20개)
실행: python eval/test_domain.py
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from domains import get_preset, ALL_PRESETS

TESTSET_PATH = Path(__file__).parent / "domain_testset.json"

# 정답 도메인명(한글) → get_preset 호출용 키워드 매핑
LABEL_TO_KEYWORD = {
    "뷰티":  "뷰티",
    "공급망": "공급망",
    "에너지": "에너지",
    "제조":  "제조",
    "물류":  "물류",
    "금융":  "금융",
    # 영문 레이블도 허용
    "beauty_ecommerce": "뷰티",
    "supply_chain":     "공급망",
    "energy":           "에너지",
    "manufacturing":    "제조",
    "logistics":        "물류",
    "finance":          "금융",
}

# 각 프리셋의 대표 키워드로 역 매핑
PRESET_TO_LABEL = {
    id(preset): label
    for label, preset in ALL_PRESETS.items()
    if label != "기타"
}


def predict_domain(sample_text: str) -> str:
    """
    sample_text를 기반으로 도메인을 예측합니다.
    get_preset()에 텍스트를 직접 전달하여 키워드 매칭으로 분류합니다.
    """
    preset = get_preset(sample_text)
    # preset 객체가 어느 도메인인지 역추적
    for label, p in ALL_PRESETS.items():
        if p is preset:
            return label
    return "기타"


def run() -> dict:
    testset = json.loads(TESTSET_PATH.read_text(encoding="utf-8"))
    if not testset:
        print("[DOMAIN] domain_testset.json이 비어 있습니다.")
        return {"accuracy": None, "correct": 0, "total": 0}

    correct = 0
    details = []
    for item in testset:
        sample_text     = item["sample_text"]
        expected_raw    = item["expected_domain"]
        expected_label  = LABEL_TO_KEYWORD.get(expected_raw, expected_raw)

        predicted = predict_domain(sample_text)

        # 예측값과 정답을 한글 레이블로 통일해 비교
        predicted_kw = LABEL_TO_KEYWORD.get(predicted, predicted)
        is_correct = (predicted_kw == expected_label)
        if is_correct:
            correct += 1

        details.append({
            "sample":    sample_text[:60] + "...",
            "expected":  expected_label,
            "predicted": predicted,
            "correct":   is_correct,
        })

    total    = len(testset)
    accuracy = round(correct / total * 100, 1) if total > 0 else 0.0

    print(f"[DOMAIN] Accuracy: {accuracy}%  ({correct}/{total})")
    for d in details:
        mark = "O" if d["correct"] else "X"
        print(f"  [{mark}] expected={d['expected']}  predicted={d['predicted']}")
        if not d["correct"]:
            print(f"       {d['sample']}")

    return {
        "accuracy": accuracy,
        "correct":  correct,
        "total":    total,
        "details":  details,
    }


if __name__ == "__main__":
    run()
