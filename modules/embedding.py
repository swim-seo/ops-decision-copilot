import logging
import time
from functools import lru_cache
from typing import List

import requests
from config import EMBEDDING_MODEL, HF_API_TOKEN

logger = logging.getLogger(__name__)

_HF_URL = f"https://api-inference.huggingface.co/models/{EMBEDDING_MODEL}"
_BATCH_SIZE = 32
_MAX_RETRIES = 3


def _call_hf(payload: dict, timeout: int = 60) -> list:
    """Call HF Inference API with cold-start retry (503 → exponential backoff)."""
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    delay = 2
    for attempt in range(_MAX_RETRIES):
        resp = requests.post(_HF_URL, headers=headers, json=payload, timeout=timeout)
        if resp.status_code == 503:
            logger.warning(
                "HF model loading (attempt %d/%d), retrying in %ds",
                attempt + 1, _MAX_RETRIES, delay,
            )
            time.sleep(delay)
            delay *= 2
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"HF Inference API unavailable after {_MAX_RETRIES} retries")


@lru_cache(maxsize=256)
def embed(text: str) -> List[float]:
    """Single text embedding with LRU cache (deduplicates identical queries)."""
    result = _call_hf({"inputs": text}, timeout=30)
    if isinstance(result, list) and result and isinstance(result[0], list):
        return result[0]
    return result


def embed_batch(texts: List[str]) -> List[List[float]]:
    """Batch embedding in groups of 32 to stay within HF free-tier limits.

    On batch failure, falls back to sequential per-chunk calls.
    """
    if not texts:
        return []

    results: List[List[float]] = []
    for i in range(0, len(texts), _BATCH_SIZE):
        batch = texts[i : i + _BATCH_SIZE]
        try:
            batch_result = _call_hf({"inputs": batch}, timeout=60)
            results.extend(batch_result)
        except Exception:
            logger.warning("Batch embed failed at offset %d, falling back to sequential", i)
            for t in batch:
                results.append(embed(t))
    return results
