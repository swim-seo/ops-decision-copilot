"""
[역할] 초기 버전 문서 파서 (현재 미사용)
PDF·DOCX 파싱만 지원하던 초기 구현체입니다.
현재는 modules/document_parser.py가 이 역할을 대체하며
CSV·Python AST 파싱 등 추가 기능이 통합되어 있습니다.
"""
import io
import PyPDF2
import docx


def parse_file(uploaded_file) -> str:
    """Streamlit UploadedFile 객체에서 텍스트를 추출합니다."""
    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        return _parse_pdf(uploaded_file)
    elif filename.endswith(".docx"):
        return _parse_docx(uploaded_file)
    elif filename.endswith(".txt") or filename.endswith(".md"):
        return uploaded_file.read().decode("utf-8")
    else:
        raise ValueError(f"지원하지 않는 파일 형식입니다: {filename}")


def _parse_pdf(file) -> str:
    reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _parse_docx(file) -> str:
    doc = docx.Document(io.BytesIO(file.read()))
    return "\n".join(para.text for para in doc.paragraphs)
