from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobRequirements(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    minimum_years: float | None = Field(default=None, ge=0, le=80)
    minimum_degree: str | None = None
    responsibilities: list[str] = Field(default_factory=list)

    @field_validator("required_skills", "preferred_skills", "responsibilities", mode="before")
    @classmethod
    def normalize_list(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.replace("；", ";").split(";") if item.strip()]
        return list(value)  # type: ignore[arg-type]


class SemanticReview(BaseModel):
    model_config = ConfigDict(extra="ignore")

    semantic_score: float = Field(ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    summary: str = ""


class MatchRequest(BaseModel):
    job_description: str = Field(min_length=20, max_length=20_000)
    use_ai_review: bool = True
