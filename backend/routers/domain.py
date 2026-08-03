import hashlib
import re
import unicodedata

from fastapi import APIRouter
from pydantic import BaseModel
from domains import get_preset

router = APIRouter()

# 슬러그 길이 상한. 값 자체는 Supabase text 라 제한이 없지만, 로그·URL 에서 읽히는
# 길이로 잘라 둔다. "domain_" 접두사를 포함한 전체 길이다.
_MAX_SLUG = 63


class DomainRequest(BaseModel):
    name: str


def _collection_name(name: str) -> str:
    """도메인명을 컬렉션 슬러그로 바꾼다.

    예전에는 `[^a-zA-Z0-9]` 를 전부 `_` 로 바꾼 뒤 `_` 를 털어냈다. 한글 이름은
    통째로 지워져 빈 문자열이 되고, 전부 `domain_default` 하나로 모였다 —
    뷰티·물류·금융을 각각 올려도 같은 컬렉션에 문서가 섞였다(RAG 교차오염).

    이제 유니코드 글자·숫자를 살린다. 컬렉션명은 Supabase text 컬럼과 URL
    쿼리 파라미터로만 흘러가고 프론트가 encodeURIComponent 를 씌우므로 한글이
    안전하다. 글자가 하나도 안 남는 이름(예: "!!!")은 원본 해시로 떨어뜨려,
    서로 다른 이름이 같은 슬러그를 갖는 일을 막는다.
    """
    # NFKC: 전각/호환 문자를 정규형으로 모아 "ＡＢ" 와 "AB" 가 갈라지지 않게 한다.
    normalized = unicodedata.normalize("NFKC", name).strip().lower()

    sanitized = re.sub(r"[^\w]", "_", normalized, flags=re.UNICODE)
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")

    if not sanitized:
        # 이름이 기호뿐이라 남는 글자가 없다. 빈 이름과 "!!!" 와 "???" 가
        # 한 컬렉션으로 뭉치지 않도록 원본에서 안정적인 해시를 만든다.
        digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
        sanitized = f"x{digest}" if name.strip() else "default"

    return f"domain_{sanitized}"[:_MAX_SLUG]


@router.post("/setup")
def setup_domain(req: DomainRequest):
    preset = get_preset(req.name)
    return {
        "collection_name": _collection_name(req.name),
        "theme_color":     preset.get("theme_color", "#f59e0b"),
        "app_icon":        preset.get("app_icon", "⚡"),
        "entity_types":    preset.get("entity_types", {}),
        "terminology":     preset.get("terminology", []),
        "analysis_focus":  preset.get("analysis_focus", []),
        "domain_context":  (
            f"도메인: {req.name}\n"
            f"주요 용어: {', '.join(preset.get('terminology', []))}\n"
            f"분석 포커스: {', '.join(preset.get('analysis_focus', []))}"
        ),
    }
