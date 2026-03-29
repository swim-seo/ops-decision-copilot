"""
[역할] Claude API 호출 래퍼
  - generate()            : 단일 프롬프트 → 텍스트 응답 (exponential backoff 재시도)
  - generate_with_system(): 시스템 프롬프트 + 유저 프롬프트 → 텍스트 응답
  - stream()              : 스트리밍 텍스트 생성 (generator yield)

API 키 조회: st.secrets → os.getenv (config._get_secret() 위임)
재시도: 429/529 → 최대 3회 (1s→2s→4s)
"""
import time
import logging
import anthropic
from config import MODEL_NAME, MAX_TOKENS, _get_secret

logger = logging.getLogger(__name__)

# ── 용도별 max_tokens 권장값 ────────────────────────────────────────────────
TOKENS = {
    "summary":    1500,
    "action":     1500,
    "root_cause": 1500,
    "report":     1500,
    "chat":       2000,
    "briefing":   2500,
    "kg":         1000,
}


class ClaudeClient:
    def __init__(self):
        api_key = _get_secret("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY가 설정되지 않았습니다. "
                "Streamlit Cloud: Settings → Secrets에 입력하세요. "
                "로컬: .env 파일에 ANTHROPIC_API_KEY=sk-ant-... 를 추가하세요."
            )
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model  = MODEL_NAME

    # ── 내부: 재시도 래퍼 ────────────────────────────────────────────────────
    def _call_with_retry(self, fn, max_retries: int = 3):
        """429/529 에러 시 exponential backoff(1→2→4초) 재시도."""
        delay = 1
        for attempt in range(max_retries):
            try:
                return fn()
            except anthropic.RateLimitError:
                if attempt == max_retries - 1:
                    raise
                logger.warning("Rate limit hit, retrying in %ss (attempt %d)", delay, attempt + 1)
                time.sleep(delay)
                delay *= 2
            except anthropic.APIStatusError as e:
                if e.status_code == 529 and attempt < max_retries - 1:
                    logger.warning("API overloaded (529), retrying in %ss", delay)
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise

    # ── 공개 메서드 ──────────────────────────────────────────────────────────
    def generate(self, prompt: str, max_tokens: int = MAX_TOKENS) -> str:
        """단일 프롬프트로 텍스트를 생성합니다 (재시도 포함)."""
        def _call():
            msg = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        return self._call_with_retry(_call)

    def generate_with_system(
        self, system: str, user: str, max_tokens: int = MAX_TOKENS
    ) -> str:
        """시스템 프롬프트와 함께 텍스트를 생성합니다 (재시도 포함)."""
        def _call():
            msg = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return msg.content[0].text
        return self._call_with_retry(_call)

    def stream(self, prompt: str, max_tokens: int = TOKENS["chat"]):
        """텍스트를 스트리밍으로 생성합니다 (generator).

        사용 예:
            for chunk in claude.stream(prompt):
                print(chunk, end="", flush=True)

        Streamlit에서는 st.write_stream(claude.stream(prompt)) 로 사용.
        """
        with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        ) as s:
            for text in s.text_stream:
                yield text
