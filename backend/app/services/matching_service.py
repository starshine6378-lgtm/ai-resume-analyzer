import re
from dataclasses import dataclass

from app.schemas.api import MatchResponse, ScoreDetails
from app.schemas.job import JobRequirements, SemanticReview
from app.schemas.resume import CandidateProfile

ALIASES = {
    "postgres": "postgresql",
    "postgre": "postgresql",
    "js": "javascript",
    "ts": "typescript",
    "fastapi": "fastapi",
    "fast api": "fastapi",
    "vuejs": "vue",
    "vue.js": "vue",
    "reactjs": "react",
    "react.js": "react",
    "k8s": "kubernetes",
    "golang": "go",
    "springboot": "spring boot",
    "es": "elasticsearch",
    "fc": "function compute",
}

DEGREE_LEVEL = {
    "高中": 1,
    "专科": 2,
    "大专": 2,
    "本科": 3,
    "学士": 3,
    "硕士": 4,
    "研究生": 4,
    "博士": 5,
}


@dataclass(frozen=True)
class SkillMatch:
    score: float
    matched: list[str]
    missing: list[str]


def normalize_skill(skill: str) -> str:
    normalized = re.sub(r"[\s._/\\-]+", " ", skill.casefold()).strip()
    compact = normalized.replace(" ", "")
    return ALIASES.get(normalized, ALIASES.get(compact, normalized))


def _has_skill(candidate_normalized: set[str], wanted: str) -> bool:
    wanted_normalized = normalize_skill(wanted)
    if wanted_normalized in candidate_normalized:
        return True
    # A conservative containment fallback handles labels such as "Python 3".
    return any(
        len(wanted_normalized) >= 3
        and (wanted_normalized in candidate or candidate in wanted_normalized)
        for candidate in candidate_normalized
    )


def calculate_skill_score(candidate: CandidateProfile, job: JobRequirements) -> SkillMatch:
    candidate_skills = list(candidate.skills)
    for project in candidate.projects:
        candidate_skills.extend(project.technologies)

    candidate_normalized = {normalize_skill(skill) for skill in candidate_skills if skill.strip()}
    required = list(dict.fromkeys(job.required_skills))
    preferred = [skill for skill in dict.fromkeys(job.preferred_skills) if skill not in required]

    matched_required = [skill for skill in required if _has_skill(candidate_normalized, skill)]
    matched_preferred = [skill for skill in preferred if _has_skill(candidate_normalized, skill)]

    required_ratio = len(matched_required) / len(required) if required else 1.0
    preferred_ratio = len(matched_preferred) / len(preferred) if preferred else 1.0

    if preferred:
        score = required_ratio * 80 + preferred_ratio * 20
    else:
        score = required_ratio * 100

    matched = matched_required + matched_preferred
    missing = [skill for skill in required + preferred if skill not in matched]
    return SkillMatch(round(score, 2), matched, missing)


def calculate_experience_score(candidate_years: float | None, minimum_years: float | None) -> float:
    if minimum_years is None or minimum_years <= 0:
        return 100.0
    if candidate_years is None:
        return 40.0
    if candidate_years >= minimum_years:
        return 100.0
    return round(max(0.0, candidate_years / minimum_years * 100), 2)


def calculate_education_score(candidate: CandidateProfile, minimum_degree: str | None) -> float:
    if not minimum_degree:
        return 100.0
    required_level = DEGREE_LEVEL.get(minimum_degree, 0)
    candidate_level = max(
        (DEGREE_LEVEL.get(item.degree or "", 0) for item in candidate.education),
        default=0,
    )
    if required_level == 0:
        return 80.0
    if candidate_level >= required_level:
        return 100.0
    if candidate_level == required_level - 1:
        return 60.0
    return 20.0


def calculate_final_score(
    skill_score: float,
    experience_score: float,
    education_score: float,
    semantic_score: float | None,
) -> float:
    if semantic_score is None:
        total = skill_score * 0.60 + experience_score * 0.30 + education_score * 0.10
    else:
        total = (
            skill_score * 0.50
            + experience_score * 0.25
            + education_score * 0.10
            + semantic_score * 0.15
        )
    return round(min(max(total, 0), 100), 2)


def recommendation_for(score: float) -> str:
    if score >= 80:
        return "strongly_recommended"
    if score >= 65:
        return "recommended"
    if score >= 50:
        return "consider"
    return "not_recommended"


def _deterministic_review(
    candidate: CandidateProfile,
    job: JobRequirements,
    skill_match: SkillMatch,
    experience_score: float,
) -> tuple[list[str], list[str], str]:
    strengths: list[str] = []
    risks: list[str] = []

    if skill_match.score >= 80:
        strengths.append("核心技能匹配度较高")
    elif skill_match.matched:
        strengths.append(f"已命中 {len(skill_match.matched)} 项岗位技能")

    if experience_score >= 100 and job.minimum_years:
        strengths.append("工作年限满足岗位要求")
    elif candidate.years_of_experience is None and job.minimum_years:
        risks.append("简历中未能可靠识别工作年限")
    elif experience_score < 100 and job.minimum_years:
        risks.append("工作年限可能低于岗位要求")

    if skill_match.missing:
        risks.append("缺少明确证据的技能：" + "、".join(skill_match.missing[:6]))
    if not candidate.projects:
        risks.append("项目经历信息较少，技术应用深度需要面试确认")

    if not strengths:
        strengths.append("候选人具备部分可迁移能力，建议结合项目细节判断")

    summary = (
        "候选人的技能和经历与岗位要求总体匹配，可进入下一轮评估。"
        if skill_match.score >= 65 and experience_score >= 60
        else "当前材料与岗位要求存在差距，建议重点核实缺失技能和相关项目经验。"
    )
    return strengths, risks, summary


def build_match_response(
    resume_id: str,
    candidate: CandidateProfile,
    job: JobRequirements,
    semantic_review: SemanticReview | None,
    cached: bool = False,
) -> MatchResponse:
    skill_match = calculate_skill_score(candidate, job)
    experience_score = calculate_experience_score(candidate.years_of_experience, job.minimum_years)
    education_score = calculate_education_score(candidate, job.minimum_degree)
    semantic_score = semantic_review.semantic_score if semantic_review else None
    total = calculate_final_score(
        skill_match.score,
        experience_score,
        education_score,
        semantic_score,
    )

    if semantic_review:
        strengths = semantic_review.strengths
        risks = semantic_review.risks
        summary = semantic_review.summary
    else:
        strengths, risks, summary = _deterministic_review(
            candidate,
            job,
            skill_match,
            experience_score,
        )

    return MatchResponse(
        resume_id=resume_id,
        cached=cached,
        score=total,
        recommendation=recommendation_for(total),  # type: ignore[arg-type]
        score_details=ScoreDetails(
            skill_score=skill_match.score,
            experience_score=experience_score,
            education_score=education_score,
            semantic_score=semantic_score,
        ),
        job_requirements=job,
        matched_keywords=skill_match.matched,
        missing_keywords=skill_match.missing,
        strengths=strengths,
        risks=risks,
        summary=summary,
        scoring_mode="ai_hybrid" if semantic_review else "deterministic",
    )
