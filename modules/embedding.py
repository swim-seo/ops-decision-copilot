"""
[역할] 텍스트 임베딩 — fastembed 로컬 ONNX (네트워크·API 키 불필요)

기존 HuggingFace Inference API(api-inference.huggingface.co) 방식은 HF 가 해당
serverless 엔드포인트를 중단해 사용 불가가 됨 → 로컬 ONNX(fastembed)로 전환.
같은 모델(paraphrase-multilingual-MiniLM-L12-v2, 384차원)이라 벡터 차원·의미가
동일 → Supabase vector(384) 스키마·기존 데이터와 호환(DB 마이그레이션 불필요).

모델은 최초 1회만 디스크로 내려받아 캐시(이후 완전 오프라인). 호출부(rag_engine,
community_summarizer)는 embed()/embed_batch() 인터페이스가 그대로라 변경 없음.
"""
import logging
from functools import lru_cache
from typing import List

from fastembed import TextEmbedding

from config import EMBEDDING_MODEL

logger = logging.getLogger(__name__)

_BATCH_SIZE = 32
_model: TextEmbedding | None = None


def _get_model() -> TextEmbedding:
    """지연 초기화 싱글턴. 최초 호출 시 모델 로드(필요하면 1회 다운로드).

    싱글턴 경합(멀티스레드)은 최악의 경우 모델을 두 번 로드하는 정도라 무해 →
    jasoseo-copilot 과 동일하게 별도 락 없이 단순 유지.
    """
    global _model
    if _model is None:
        logger.info("fastembed 모델 로드: %s", EMBEDDING_MODEL)
        _model = TextEmbedding(model_name=EMBEDDING_MODEL)
    return _model


def embed_batch(texts: List[str]) -> List[List[float]]:
    """텍스트 목록을 로컬에서 임베딩합니다 (배치 크기 32).

    HF API 시절의 '배치 실패 시 순차 폴백'은 불필요 — 로컬 추론이라 네트워크
    실패 지점이 없다(모델 로드만 성공하면 계산은 결정적).
    """
    if not texts:
        return []
    model = _get_model()
    return [vec.tolist() for vec in model.embed(texts, batch_size=_BATCH_SIZE)]


@lru_cache(maxsize=256)
def embed(text: str) -> List[float]:
    """단일 텍스트 임베딩 (동일 질의 LRU 캐시로 중복 계산 방지)."""
    return embed_batch([text])[0]
