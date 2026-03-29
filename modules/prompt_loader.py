"""
[역할] 프롬프트 템플릿 파일 로더
prompts/ 폴더의 .txt 파일을 읽어 플레이스홀더({변수명})를 실제 값으로 치환합니다.
  - load_prompt("summarize", document="...")  → prompts/summarize.txt 로드 후 치환
  - load_prompt("rag_query", question="...", context="...")
프롬프트를 코드와 분리해 관리하므로, 프롬프트 수정 시 Python 코드를 건드릴 필요가 없습니다.
"""
import os
from typing import Dict

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")


def _load_system_base() -> str:
    """system_base.txt의 공통 프롬프트를 로드합니다 (캐시)."""
    if not hasattr(_load_system_base, "_cache"):
        base_path = os.path.join(PROMPTS_DIR, "system_base.txt")
        if os.path.exists(base_path):
            with open(base_path, "r", encoding="utf-8") as f:
                _load_system_base._cache = f.read()
        else:
            _load_system_base._cache = ""
    return _load_system_base._cache


def load_prompt(name: str, **kwargs) -> str:
    """
    prompts/{name}.txt 파일을 읽고 플레이스홀더를 치환합니다.
    {system_base} 플레이스홀더가 있으면 system_base.txt 내용으로 치환합니다.

    사용 예:
        load_prompt("summarize", document="...", domain_context="...")
        load_prompt("rag_query", question="...", context="...", domain_context="...")
    """
    path = os.path.join(PROMPTS_DIR, f"{name}.txt")
    if not os.path.exists(path):
        raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {path}")

    with open(path, "r", encoding="utf-8") as f:
        template = f.read()

    # system_base 주입
    if "{system_base}" in template:
        template = template.replace("{system_base}", _load_system_base())

    for key, value in kwargs.items():
        template = template.replace("{" + key + "}", str(value))

    return template
