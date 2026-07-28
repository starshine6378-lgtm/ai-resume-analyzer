from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.job import JobRequirements
from app.schemas.resume import CandidateProfile


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str | None = None
    details: object | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str
    environment: str
    ai_enabled: bool
    cache_backend: str


class ResumeAnalysisResponse(BaseModel):
    resume_id: str
    cached: bool
    filename: str
    page_count: int
    raw_text_length: int
    extraction_mode: Literal["ai", "rules", "hybrid"]
    candidate: CandidateProfile
    text_preview: str
    warnings: list[str] = Field(default_factory=list)


class ScoreDetails(BaseModel):
    skill_score: float
    experience_score: float
    education_score: float
    semantic_score: float | None = None


class MatchResponse(BaseModel):
    resume_id: str
    cached: bool = False
    score: float
    recommendation: Literal[
        "strongly_recommended",
        "recommended",
        "consider",
        "not_recommended",
    ]
    score_details: ScoreDetails
    job_requirements: JobRequirements
    matched_keywords: list[str]
    missing_keywords: list[str]
    strengths: list[str]
    risks: list[str]
    summary: str
    scoring_mode: Literal["ai_hybrid", "deterministic"]


class AnalyzeAndMatchResponse(BaseModel):
    analysis: ResumeAnalysisResponse
    match: MatchResponse
