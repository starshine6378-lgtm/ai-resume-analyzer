from app.services.text_cleaner import clean_resume_text


def test_clean_resume_text_removes_duplicate_lines_and_page_markers() -> None:
    raw = """
    --- 第 1 页 ---
    张三
    Python 开发工程师
    页脚
    --- 第 2 页 ---
    工作经历
    工作经历
    页脚
    --- 第 3 页 ---
    项目经历
    页脚
    """
    cleaned = clean_resume_text(raw)
    assert "--- 第" not in cleaned
    assert cleaned.count("工作经历") == 1
    assert "页脚" not in cleaned
