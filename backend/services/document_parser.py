"""
document_parser.py - Multi-format document parsing pipeline for LexGuard.

Handles PDF (native + OCR), DOCX, and plain-text files, returning clean
extracted text along with metadata such as page count.
"""

import io
import logging
from typing import Optional

from ..utils.constants import MAX_FILE_SIZE_BYTES, PDF_MAGIC, DOCX_MAGIC

logger = logging.getLogger(__name__)


def _validate_magic_bytes(data: bytes, extension: str) -> None:
    """Verify file magic bytes match the claimed extension.

    Args:
        data: Raw file bytes.
        extension: Lowercase file extension without the leading dot.

    Raises:
        ValueError: If magic bytes do not match the claimed type.
    """
    if extension == "pdf" and not data.startswith(PDF_MAGIC):
        raise ValueError("File does not appear to be a valid PDF (magic bytes mismatch).")
    if extension == "docx" and not data.startswith(DOCX_MAGIC):
        raise ValueError("File does not appear to be a valid DOCX (magic bytes mismatch).")


def _extract_text_from_pdf(data: bytes) -> tuple[str, int]:
    """Extract text from a PDF using PyMuPDF; fall back to Tesseract OCR.

    Args:
        data: Raw PDF bytes.

    Returns:
        Tuple of (extracted_text, page_count).

    Raises:
        ValueError: If text extraction fails entirely.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise ImportError("PyMuPDF (fitz) is not installed.") from exc

    pages_text: list[str] = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        page_count = doc.page_count
        for page in doc:
            text = page.get_text("text")
            if text.strip():
                pages_text.append(text)
            else:
                pages_text.append(_ocr_page(page))

    full_text = "\n\n".join(pages_text).strip()
    if not full_text:
        raise ValueError("Could not extract any readable text from the PDF.")
    return full_text, page_count


def _ocr_page(page) -> str:  # type: ignore[no-untyped-def]
    """Apply Tesseract OCR to a single PyMuPDF page.

    Args:
        page: PyMuPDF page object.

    Returns:
        OCR-extracted text string (may be empty if OCR fails).
    """
    try:
        import pytesseract
        from PIL import Image
        import fitz

        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return pytesseract.image_to_string(img)
    except Exception as exc:
        logger.warning("OCR failed for page: %s", exc)
        return ""


def _extract_text_from_docx(data: bytes) -> tuple[str, int]:
    """Extract text from a DOCX file using python-docx.

    Args:
        data: Raw DOCX bytes.

    Returns:
        Tuple of (extracted_text, paragraph_count).

    Raises:
        ValueError: If the DOCX cannot be read.
    """
    try:
        from docx import Document
    except ImportError as exc:
        raise ImportError("python-docx is not installed.") from exc

    stream = io.BytesIO(data)
    doc = Document(stream)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    full_text = "\n\n".join(paragraphs)
    if not full_text:
        raise ValueError("Could not extract any readable text from the DOCX.")
    return full_text, len(paragraphs)


def _extract_text_from_txt(data: bytes) -> tuple[str, int]:
    """Decode plain-text file bytes to a string.

    Args:
        data: Raw file bytes.

    Returns:
        Tuple of (decoded_text, line_count).

    Raises:
        ValueError: If the bytes cannot be decoded as text.
    """
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            text = data.decode(encoding)
            lines = [ln for ln in text.splitlines() if ln.strip()]
            return text, len(lines)
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not decode the text file with any supported encoding.")


def parse_document(
    data: bytes,
    filename: str,
    content_type: Optional[str] = None,
) -> dict:
    """Parse an uploaded document and return extracted text with metadata.

    Args:
        data: Raw file bytes (in-memory, never written to disk).
        filename: Original filename (used to determine file type).
        content_type: Optional MIME type for secondary type detection.

    Returns:
        Dictionary with keys:
            - ``text`` (str): Extracted document text.
            - ``page_count`` (int): Number of pages / paragraphs.
            - ``file_type`` (str): Detected file type extension.
            - ``char_count`` (int): Length of extracted text.

    Raises:
        ValueError: For unsupported formats, bad magic bytes, or empty text.
    """
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES} bytes.")

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    _validate_magic_bytes(data, ext)

    if ext == "pdf":
        text, pages = _extract_text_from_pdf(data)
    elif ext == "docx":
        text, pages = _extract_text_from_docx(data)
    elif ext == "txt":
        text, pages = _extract_text_from_txt(data)
    else:
        raise ValueError(f"Unsupported file type: '{ext}'. Allowed: pdf, docx, txt.")

    return {
        "text": text,
        "page_count": pages,
        "file_type": ext,
        "char_count": len(text),
    }
