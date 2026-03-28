"""
[역할] Gemini API 클라이언트 (현재 미사용)
초기 프로토타입 단계에서 Google Gemini를 AI 엔진으로 사용하던 클라이언트입니다.
현재 앱은 Claude(Anthropic)로 전환되었으므로 이 파일은 사용되지 않습니다.
"""
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


def get_client() -> genai.GenerativeModel:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")


def generate(prompt: str) -> str:
    model = get_client()
    response = model.generate_content(prompt)
    return response.text
