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
