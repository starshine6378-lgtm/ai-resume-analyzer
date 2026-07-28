from app.schemas.job import JobRequirements
from app.schemas.resume import CandidateProfile, Education, Project
from app.services.matching_service import build_match_response, calculate_skill_score


def test_skill_alias_and_project_technologies_are_matched() -> None:
    candidate = CandidateProfile(
        skills=["Python", "K8s"],
        projects=[Project(name="订单系统", technologies=["Fast API", "Redis"])],
    )
    job = JobRequirements(
        required_skills=["Python", "FastAPI", "Kubernetes", "Redis"],
    )
    result = calculate_skill_score(candidate, job)
    assert result.score == 100
    assert result.missing == []


def test_deterministic_match_returns_explainable_score() -> None:
    candidate = CandidateProfile(
        years_of_experience=4,
        skills=["Python", "FastAPI", "Redis", "Docker"],
        education=[Education(degree="本科")],
        projects=[Project(name="API 平台", technologies=["FastAPI", "Redis"])],
    )
    job = JobRequirements(
        required_skills=["Python", "FastAPI", "Redis"],
        preferred_skills=["Kubernetes"],
        minimum_years=3,
        minimum_degree="本科",
    )
    response = build_match_response("abc", candidate, job, semantic_review=None)
    assert response.score >= 80
    assert response.scoring_mode == "deterministic"
    assert "Kubernetes" in response.missing_keywords
