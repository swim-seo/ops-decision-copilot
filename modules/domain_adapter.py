"""도메인 적응형 설정 모듈 - Claude AI 기반 동적 도메인 분석"""
import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class DomainConfig:
    name: str
    description: str
    entity_types: Dict[str, str]   # {type_name: color_hex}
    terminology: List[str]
    document_patterns: List[str]
    analysis_focus: List[str]
    theme_color: str
    app_title: str
    app_icon: str

    def to_context_string(self) -> str:
        """모든 Claude 프롬프트에 주입할 도메인 컨텍스트 문자열"""
        return (
            f"도메인: {self.name}\n"
            f"도메인 설명: {self.description}\n"
            f"핵심 용어/개념: {', '.join(self.terminology)}\n"
            f"주요 문서 유형: {', '.join(self.document_patterns)}\n"
            f"분석 포커스: {', '.join(self.analysis_focus)}\n"
            f"주요 엔티티 유형: {', '.join(self.entity_types.keys())}"
        )

    def get_entity_types_description(self) -> str:
        """지식 그래프 엔티티 추출 프롬프트용 엔티티 유형 설명"""
        _hints = {
            "person":       "사람, 담당자, 직책",
            "organization": "조직, 회사, 팀, 기관",
            "issue":        "문제, 이슈, 리스크",
            "decision":     "결정 사항, 의사결정",
            "metric":       "지표, KPI, 수치",
            "process":      "프로세스, 절차, 워크플로",
            "resource":     "자원, 도구, 시스템, 장비",
            "product":      "제품, 서비스, 솔루션",
            "event":        "이벤트, 일정, 마일스톤",
            "location":     "장소, 지역, 시설",
        }
        lines = []
        for etype in self.entity_types:
            hint = _hints.get(etype, f"{etype} 관련 엔티티")
            lines.append(f"- {etype}: {hint}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "entity_types": self.entity_types,
            "terminology": self.terminology,
            "document_patterns": self.document_patterns,
            "analysis_focus": self.analysis_focus,
            "theme_color": self.theme_color,
            "app_title": self.app_title,
            "app_icon": self.app_icon,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainConfig":
        return cls(**data)

    @property
    def collection_name(self) -> str:
        """RAG 컬렉션 이름 (ChromaDB 최대 63자, 영숫자+언더스코어)"""
        sanitized = re.sub(r"[^a-zA-Z0-9]", "_", self.name)
        sanitized = re.sub(r"_+", "_", sanitized).strip("_").lower()
        return f"domain_{sanitized or 'default'}"[:63]


class DomainAdapter:
    def __init__(self, claude_client):
        self.client = claude_client

    def analyze_domain(self, domain_name: str, domain_description: str) -> DomainConfig:
        """Claude를 이용해 도메인을 분석하고 DomainConfig를 반환합니다."""
        prompt = self._build_prompt(domain_name, domain_description)
        try:
            response = self.client.generate(prompt, max_tokens=2000)
            return self._parse_response(domain_name, domain_description, response)
        except Exception:
            return self._default_config(domain_name, domain_description)

    def _build_prompt(self, domain_name: str, domain_description: str) -> str:
        return f"""당신은 다양한 비즈니스 도메인을 분석하는 전문가입니다.

아래 도메인 정보를 분석하여 AI 운영 코파일럿에 필요한 설정을 JSON으로 반환하세요.

도메인명: {domain_name}
도메인 설명: {domain_description}

아래 JSON 형식으로만 답변하세요 (마크다운 코드블록 없이, 순수 JSON):
{{
  "entity_types": {{
    "유형명1": "#16진수색상",
    "유형명2": "#16진수색상",
    "issue": "#F44336",
    "decision": "#4CAF50"
  }},
  "terminology": ["핵심용어1", "핵심용어2"],
  "document_patterns": ["문서유형1", "문서유형2"],
  "analysis_focus": ["분석포커스1", "분석포커스2"],
  "theme_color": "#16진수색상",
  "app_title": "{domain_name} AI 운영 코파일럿",
  "app_icon": "이모지"
}}

규칙:
- entity_types: 6~10개, 반드시 "issue"와 "decision" 포함
- terminology: 10~15개의 도메인 핵심 전문 용어
- document_patterns: 5~8개의 주요 문서 유형 (회의록, 보고서 등)
- analysis_focus: 5~8개의 주요 분석 영역
- theme_color: 이 도메인 이미지에 어울리는 색상
- app_icon: 도메인을 표현하는 단일 이모지"""

    def _parse_response(
        self, domain_name: str, domain_description: str, response: str
    ) -> DomainConfig:
        # 마크다운 코드블록 내 JSON 우선 추출
        code_block = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
        if code_block:
            candidate = code_block.group(1).strip()
        else:
            json_match = re.search(r"\{[\s\S]*\}", response)
            if not json_match:
                return self._default_config(domain_name, domain_description)
            candidate = json_match.group()

        # 후행 쉼표 제거
        candidate = re.sub(r",\s*([}\]])", r"\1", candidate)

        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            return self._default_config(domain_name, domain_description)

        entity_types = data.get("entity_types", {})
        entity_types.setdefault("issue", "#F44336")
        entity_types.setdefault("decision", "#4CAF50")

        return DomainConfig(
            name=domain_name,
            description=domain_description,
            entity_types=entity_types,
            terminology=data.get("terminology", []),
            document_patterns=data.get("document_patterns", []),
            analysis_focus=data.get("analysis_focus", []),
            theme_color=data.get("theme_color", "#2196F3"),
            app_title=data.get("app_title", f"{domain_name} AI 운영 코파일럿"),
            app_icon=data.get("app_icon", "🤖"),
        )

    def _default_config(self, domain_name: str, domain_description: str) -> DomainConfig:
        return DomainConfig(
            name=domain_name,
            description=domain_description,
            entity_types={
                "person":       "#2196F3",
                "organization": "#9C27B0",
                "process":      "#FF9800",
                "resource":     "#00BCD4",
                "issue":        "#F44336",
                "decision":     "#4CAF50",
                "metric":       "#607D8B",
                "default":      "#9E9E9E",
            },
            terminology=[],
            document_patterns=["회의록", "보고서", "정책 문서", "분석 자료"],
            analysis_focus=["핵심 의사결정", "리스크", "실행 과제", "성과 지표"],
            theme_color="#2196F3",
            app_title=f"{domain_name} AI 운영 코파일럿",
            app_icon="🤖",
        )
