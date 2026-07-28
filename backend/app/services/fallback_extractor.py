import re
from datetime import date

from app.schemas.job import JobRequirements
from app.schemas.resume import CandidateProfile, Education, Project

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)")
SALARY_RE = re.compile(
    r"(?:期望薪资|薪资期望|期望待遇|薪酬要求)\s*[:：]?\s*([^\n]{2,30})",
    re.IGNORECASE,
)
YEARS_RE = re.compile(
    r"(?P<years>\d+(?:\.\d+)?)\s*(?:年(?:以上)?(?:工作|开发|从业)?经验|"
    r"years?(?:\s+of)?\s+(?:work|development)?\s*experience)",
    re.IGNORECASE,
)
MIN_YEARS_RE = re.compile(
    r"(?:至少|不少于|具备|要求)?\s*(\d+(?:\.\d+)?)\s*年"
    r"(?:以上)?(?:相关)?(?:工作|开发|项目)?经验"
)
DATE_RANGE_RE = re.compile(
    r"(?P<sy>19\d{2}|20\d{2})[./年-](?P<sm>\d{1,2})?\s*(?:-|—|~|至)\s*"
    r"(?:(?P<ey>19\d{2}|20\d{2})[./年-]?(?P<em>\d{1,2})?|(?P<present>至今|现在))"
)

SKILL_PATTERNS: dict[str, tuple[str, ...]] = {
    "Python": (r"\bpython\b",),
    "Java": (r"\bjava\b",),
    "Go": (r"\bgolang\b", r"\bgo语言\b"),
    "JavaScript": (r"\bjavascript\b", r"\bjs\b"),
    "TypeScript": (r"\btypescript\b", r"\bts\b"),
    "FastAPI": (r"\bfast\s*api\b",),
    "Flask": (r"\bflask\b",),
    "Django": (r"\bdjango\b",),
    "Spring Boot": (r"\bspring\s*boot\b",),
    "React": (r"\breact(?:\.js|js)?\b",),
    "Vue": (r"\bvue(?:\.js|js)?\b",),
    "MySQL": (r"\bmysql\b",),
    "PostgreSQL": (r"\bpostgres(?:ql)?\b",),
    "MongoDB": (r"\bmongodb\b",),
    "Redis": (r"\bredis\b",),
    "Elasticsearch": (r"\belasticsearch\b", r"\bes\b"),
    "Docker": (r"\bdocker\b",),
    "Kubernetes": (r"\bkubernetes\b", r"\bk8s\b"),
    "Linux": (r"\blinux\b",),
    "Git": (r"\bgit\b",),
    "Nginx": (r"\bnginx\b",),
    "Kafka": (r"\bkafka\b",),
    "RabbitMQ": (r"\brabbitmq\b",),
    "Celery": (r"\bcelery\b",),
    "RESTful API": (r"\brestful\b", r"\brest api\b"),
    "微服务": (r"微服务", r"microservices?"),
    "Serverless": (r"\bserverless\b", r"函数计算"),
    "阿里云": (r"阿里云", r"aliyun", r"alibaba cloud"),
    "AWS": (r"\baws\b",),
    "LLM": (r"\bllm\b", r"大语言模型", r"大模型"),
    "RAG": (r"\brag\b", r"检索增强生成"),
    "PyTorch": (r"\bpytorch\b",),
    "TensorFlow": (r"\btensorflow\b",),
    "SQL": (r"\bsql\b",),
}

DEGREES = ("博士", "硕士", "研究生", "本科", "学士", "大专", "专科", "高中")
PREFERRED_MARKERS = ("优先", "加分", "更佳", "最好", "preferred", "plus")


def extract_skills(text: str) -> list[str]:
    lowered = text.casefold()
    skills: list[str] = []
    for canonical, patterns in SKILL_PATTERNS.items():
        if any(re.search(pattern, lowered, re.IGNORECASE) for pattern in patterns):
            skills.append(canonical)
    return skills


def _extract_name(lines: list[str]) -> str | None:
    banned = ("简历", "求职", "电话", "邮箱", "工作", "经验", "技能", "教育", "resume")
    for line in lines[:12]:
        candidate = re.sub(r"^(姓名|name)\s*[:：]\s*", "", line, flags=re.IGNORECASE).strip()
        if any(word in candidate.casefold() for word in banned):
            continue
        if re.fullmatch(r"[\u4e00-\u9fff·]{2,8}", candidate):
            return candidate
        if re.fullmatch(r"[A-Za-z][A-Za-z .'-]{2,40}", candidate) and len(candidate.split()) <= 5:
            return candidate
    return None


def _extract_address(lines: list[str]) -> str | None:
    for line in lines:
        match = re.search(
            r"(?:现居住地|现居地|所在地|地址|location)\s*[:：]\s*([^|｜,，;；]{2,40})",
            line,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()
    return None


def _extract_job_intention(lines: list[str]) -> str | None:
    for line in lines:
        match = re.search(r"(?:求职意向|目标岗位|应聘职位|期望职位)\s*[:：]\s*(.{2,60})", line)
        if match:
            return match.group(1).strip()
    return None


def _calculate_years_from_ranges(text: str) -> float | None:
    total_months = 0
    current = date.today()
    ranges = list(DATE_RANGE_RE.finditer(text))
    for match in ranges:
        sy = int(match.group("sy"))
        sm = int(match.group("sm") or 1)
        if match.group("present"):
            ey, em = current.year, current.month
        else:
            ey = int(match.group("ey") or sy)
            em = int(match.group("em") or 12)
        months = (ey - sy) * 12 + (em - sm)
        if 0 < months < 600:
            total_months += months
    if total_months == 0:
        return None
    # Date ranges can overlap, so cap at elapsed time since the earliest plausible job.
    return round(min(total_months / 12, 50), 1)


def _extract_education(lines: list[str]) -> list[Education]:
    result: list[Education] = []
    for line in lines:
        degree = next((item for item in DEGREES if item in line), None)
        if not degree:
            continue
        school_match = re.search(
            r"([\u4e00-\u9fffA-Za-z· ]{2,30}(?:大学|学院|University|College))",
            line,
            re.IGNORECASE,
        )
        major_match = re.search(
            r"(?:专业|major)\s*[:：]?\s*([\u4e00-\u9fffA-Za-z+.# ]{2,30})",
            line,
            re.IGNORECASE,
        )
        education = Education(
            school=school_match.group(1).strip() if school_match else None,
            degree=degree,
            major=major_match.group(1).strip() if major_match else None,
        )
        if education not in result:
            result.append(education)
    return result[:6]


def _section_lines(lines: list[str], heading_words: tuple[str, ...], limit: int = 8) -> list[str]:
    collecting = False
    result: list[str] = []
    section_words = ("教育", "工作", "项目", "技能", "自我", "证书", "获奖", "个人")
    for line in lines:
        stripped = line.strip("：: ")
        if any(word in stripped for word in heading_words) and len(stripped) <= 12:
            collecting = True
            continue
        if collecting and any(word in stripped for word in section_words) and len(stripped) <= 12:
            break
        if collecting:
            result.append(line)
            if len(result) >= limit:
                break
    return result


def extract_candidate_rules(text: str) -> CandidateProfile:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    email_match = EMAIL_RE.search(text)
    phone_match = PHONE_RE.search(text)
    salary_match = SALARY_RE.search(text)
    explicit_years = YEARS_RE.search(text)
    project_lines = _section_lines(lines, ("项目经历", "项目经验"), limit=12)
    work_lines = _section_lines(lines, ("工作经历", "工作经验"), limit=12)

    projects: list[Project] = []
    if project_lines:
        projects.append(
            Project(
                name=project_lines[0][:80],
                description="；".join(project_lines[1:6]) or project_lines[0],
                technologies=extract_skills("\n".join(project_lines)),
            )
        )

    return CandidateProfile(
        name=_extract_name(lines),
        phone=phone_match.group(0) if phone_match else None,
        email=email_match.group(0) if email_match else None,
        address=_extract_address(lines),
        job_intention=_extract_job_intention(lines),
        expected_salary=salary_match.group(1).strip() if salary_match else None,
        years_of_experience=(
            float(explicit_years.group("years"))
            if explicit_years
            else _calculate_years_from_ranges(text)
        ),
        education=_extract_education(lines),
        skills=extract_skills(text),
        projects=projects,
        work_experience=work_lines[:8],
    )


def extract_job_rules(job_description: str) -> JobRequirements:
    lines = [line.strip(" •●-\t") for line in job_description.splitlines() if line.strip()]
    required: list[str] = []
    preferred: list[str] = []

    for line in lines:
        skills = extract_skills(line)
        is_preferred = any(marker in line.casefold() for marker in PREFERRED_MARKERS)
        target = preferred if is_preferred else required
        for skill in skills:
            if skill not in target:
                target.append(skill)

    # Skills mentioned only in the title or a single-paragraph JD still count as required.
    for skill in extract_skills(job_description):
        if skill not in required and skill not in preferred:
            required.append(skill)

    years_match = MIN_YEARS_RE.search(job_description)
    degree = next((item for item in DEGREES if item in job_description), None)
    title = lines[0][:80] if lines else None
    responsibilities = [
        line
        for line in lines
        if any(marker in line for marker in ("负责", "职责", "参与", "设计", "开发"))
    ][:8]

    return JobRequirements(
        title=title,
        required_skills=required,
        preferred_skills=preferred,
        minimum_years=float(years_match.group(1)) if years_match else None,
        minimum_degree=degree,
        responsibilities=responsibilities,
    )
