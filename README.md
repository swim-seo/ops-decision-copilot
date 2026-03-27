# ops-decision-copilot
> 사내 문서 기반 AI 의사결정 지원 시스템

## 개요
Claude API + ChromaDB 기반 RAG 파이프라인을 활용해
내부 문서를 자동 분석하고 의사결정을 지원하는 AI 시스템입니다.

## 핵심 기능
| 기능 | 설명 |
|---|---|
| 문서 업로드 | PDF·DOCX·TXT 자동 청킹 → ChromaDB 벡터 인덱싱 |
| AI 분석 | 요약 / 액션 아이템 / 원인분석(5-Why) / 보고서 초안 |
| 문서 검색 | 자연어 질의 → 시맨틱 검색 → 출처 기반 답변 |
| 지식 그래프 | 문서 간 관계 인터랙티브 시각화 (NetworkX) |

## 기술 스택
- LLM: Claude API (Anthropic)
- 벡터DB: ChromaDB
- 임베딩: paraphrase-multilingual-MiniLM-L12-v2 (한국어 최적화)
- UI: Streamlit
- 그래프: NetworkX + pyvis

## 실행 방법
```bash
cp .env.example .env
# ANTHROPIC_API_KEY 입력
pip install -r requirements.txt
streamlit run app.py
```
