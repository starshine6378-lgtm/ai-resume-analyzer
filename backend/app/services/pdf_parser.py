from dataclasses import dataclass

import fitz

from app.core.errors import AppError


@dataclass(frozen=True)
class ParsedPDF:
    text: str
    page_count: int


def extract_pdf_text(pdf_bytes: bytes) -> ParsedPDF:
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise AppError("INVALID_PDF", "无法读取 PDF，文件可能已损坏", 422) from exc

    try:
        if document.needs_pass:
            raise AppError("ENCRYPTED_PDF", "暂不支持加密 PDF", 422)
        if document.page_count == 0:
            raise AppError("EMPTY_PDF", "PDF 不包含有效页面", 422)

        pages: list[str] = []
        for page_number, page in enumerate(document, start=1):
            try:
                page_text = page.get_text("text", sort=True).strip()
            except Exception:
                page_text = page.get_text("text").strip()
            if page_text:
                pages.append(f"--- 第 {page_number} 页 ---\n{page_text}")

        text = "\n\n".join(pages).strip()
        if len(text) < 30:
            raise AppError(
                "PDF_TEXT_NOT_FOUND",
                "未提取到足够文本；该文件可能是扫描版 PDF，请先进行 OCR",
                422,
            )
        return ParsedPDF(text=text, page_count=document.page_count)
    finally:
        document.close()
