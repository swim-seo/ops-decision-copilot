import re
from fastapi import APIRouter
from pydantic import BaseModel
from domains import get_preset

router = APIRouter()


class DomainRequest(BaseModel):
    name: str


def _collection_name(name: str) -> str:
    sanitized = re.sub(r"[^a-zA-Z0-9]", "_", name)
    sanitized = re.sub(r"_+", "_", sanitized).strip("_").lower()
    return f"domain_{sanitized or 'default'}"[:63]


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
