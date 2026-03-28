"""
[역할] 도메인 프리셋 패키지
각 파일에 도메인별 entity_types, terminology, theme_color 등을 정의합니다.
새 도메인 추가: 새 파일 생성 후 이 __init__.py에 등록하면 앱 전체에 자동 반영됩니다.
"""
from domains.beauty        import PRESET as _beauty
from domains.supply_chain  import PRESET as _supply_chain
from domains.energy        import PRESET as _energy
from domains.manufacturing import PRESET as _manufacturing
from domains.logistics     import PRESET as _logistics
from domains.finance       import PRESET as _finance
from domains.generic       import PRESET as _generic

ALL_PRESETS: dict = {
    "뷰티":   _beauty,
    "공급망":  _supply_chain,
    "에너지":  _energy,
    "제조":   _manufacturing,
    "물류":   _logistics,
    "금융":   _finance,
    "기타":   _generic,
}


def get_preset(name: str) -> dict:
    """도메인 이름으로 프리셋 반환. 매칭 실패 시 generic 반환."""
    n = name.upper()
    if any(k in n for k in ["뷰티", "BEAUTY", "화장품", "COSMETIC", "이커머스"]):
        return _beauty
    if any(k in n for k in ["공급", "SUPPLY", "재고", "INVENTORY", "발주", "창고"]):
        return _supply_chain
    if any(k in n for k in ["에너지", "ENERGY", "발전"]):
        return _energy
    if any(k in n for k in ["제조", "MANUF", "생산", "FACTORY"]):
        return _manufacturing
    if any(k in n for k in ["물류", "LOGISTIC", "배송"]):
        return _logistics
    if any(k in n for k in ["금융", "FINANC", "투자", "회계"]):
        return _finance
    return _generic
