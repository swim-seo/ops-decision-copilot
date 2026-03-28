"""
[역할] Claude API 호출 래퍼
Anthropic SDK를 감싸서 앱 전역에서 일관된 방식으로 Claude를 호출합니다.
  - generate(prompt)          : 단일 프롬프트 → 텍스트 응답
  - generate_with_system(...) : 시스템 프롬프트 + 유저 프롬프트 → 텍스트 응답
모든 AI 기능(요약·분석·도메인 분석·KG 추출)이 이 클래스를 통해 Claude를 호출합니다.
"""
import anthropic
from config import ANTHROPIC_API_KEY, MODEL_NAME, MAX_TOKENS


class ClaudeClient:
    def __init__(self):
        if not ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY가 설정되지 않았습니다. "
                ".env 파일에 API 키를 입력해주세요."
            )
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = MODEL_NAME

    def generate(self, prompt: str, max_tokens: int = MAX_TOKENS) -> str:
        """단일 프롬프트로 텍스트를 생성합니다."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    def generate_with_system(
        self, system: str, user: str, max_tokens: int = MAX_TOKENS
    ) -> str:
        """시스템 프롬프트와 함께 텍스트를 생성합니다."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return message.content[0].text
