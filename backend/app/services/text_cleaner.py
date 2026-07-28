import re
import unicodedata
from collections import Counter

SECTION_HEADINGS = {
    "个人信息",
    "基本信息",
    "求职意向",
    "教育经历",
    "教育背景",
    "工作经历",
    "工作经验",
    "项目经历",
    "项目经验",
    "专业技能",
    "技能",
    "自我评价",
    "个人优势",
    "证书",
    "获奖经历",
}


def _is_page_marker(line: str) -> bool:
    return bool(re.fullmatch(r"---\s*第\s*\d+\s*页\s*---", line))


def clean_resume_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    raw_lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    raw_lines = [line for line in raw_lines if line]

    # Remove short lines repeated specifically in page margins, rather than
    # deleting legitimate skills that happen to appear several times.
    pages: list[list[str]] = []
    current_page: list[str] = []
    for line in raw_lines:
        if _is_page_marker(line):
            if current_page:
                pages.append(current_page)
                current_page = []
            continue
        current_page.append(line)
    if current_page:
        pages.append(current_page)

    counts: Counter[str] = Counter()
    for page in pages:
        page_margins = {
            line for line in [*page[:2], *page[-2:]] if 2 <= len(line) <= 40
        }
        counts.update(page_margins)
    repeated_noise = {line for line, count in counts.items() if count >= 2}

    result: list[str] = []
    previous = ""
    for line in raw_lines:
        if _is_page_marker(line) or line in repeated_noise:
            continue
        line = re.sub(r"^[•●▪■◆◇►▶]+\s*", "• ", line)
        if line == previous:
            continue
        if line.rstrip(":：") in SECTION_HEADINGS and result and result[-1] != "":
            result.append("")
        result.append(line)
        previous = line

    cleaned = "\n".join(result)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()
