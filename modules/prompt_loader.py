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


def load_prompt(name: str, **kwargs) -> str:
    """
    prompts/{name}.txt 파일을 읽고 플레이스홀더를 치환합니다.

    사용 예:
        load_prompt("summarize", document="...")
        load_prompt("rag_query", question="...", context="...")
    """
    path = os.path.join(PROMPTS_DIR, f"{name}.txt")
    if not os.path.exists(path):
        raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {path}")

    with open(path, "r", encoding="utf-8") as f:
        template = f.read()

    for key, value in kwargs.items():
        template = template.replace("{" + key + "}", str(value))

    return template
