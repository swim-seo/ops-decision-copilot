"""문서 파싱 및 청킹 모듈 (PDF, DOCX, TXT/MD 지원)"""
import io
import PyPDF2
import docx
from typing import List


def parse_file(uploaded_file) -> str:
    """Streamlit UploadedFile 객체에서 텍스트를 추출합니다."""
    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        return _parse_pdf(uploaded_file)
    elif filename.endswith(".docx"):
        return _parse_docx(uploaded_file)
    elif filename.endswith((".txt", ".md")):
        return uploaded_file.read().decode("utf-8")
    else:
        raise ValueError(f"지원하지 않는 파일 형식입니다: {filename}")


def _parse_pdf(file) -> str:
    reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _parse_docx(file) -> str:
    doc = docx.Document(io.BytesIO(file.read()))
    return "\n".join(para.text for para in doc.paragraphs)


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
    """텍스트를 오버랩이 있는 청크로 분할합니다."""
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # 문장/단락 경계에서 자르기
        if end < len(text):
            for sep in ["\n\n", "\n", ". ", "。", " "]:
                idx = chunk.rfind(sep)
                if idx > chunk_size // 2:
                    chunk = chunk[: idx + len(sep)]
                    end = start + idx + len(sep)
                    break

        chunk = chunk.strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap

    return chunks
