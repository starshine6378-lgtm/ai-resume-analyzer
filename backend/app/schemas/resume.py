from pydantic import BaseModel, ConfigDict, Field, field_validator


class Education(BaseModel):
    model_config = ConfigDict(extra="ignore")

    school: str | None = None
    degree: str | None = None
    major: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)

    @field_validator("technologies", mode="before")
    @classmethod
    def technologies_must_be_list(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.replace("，", ",").split(",") if item.strip()]
        return list(value)  # type: ignore[arg-type]


class CandidateProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None

    job_intention: str | None = None
    expected_salary: str | None = None

    years_of_experience: float | None = Field(default=None, ge=0, le=80)
    education: list[Education] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    work_experience: list[str] = Field(default_factory=list)

    @field_validator("skills", "work_experience", mode="before")
    @classmethod
    def string_or_list(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            separator_normalized = value.replace("；", ";").replace("，", ",")
            return [
                item.strip()
                for item in separator_normalized.replace(";", ",").split(",")
                if item.strip()
            ]
        return list(value)  # type: ignore[arg-type]

    @field_validator("skills")
    @classmethod
    def deduplicate_skills(cls, value: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for skill in value:
            cleaned = skill.strip()
            key = cleaned.casefold()
            if cleaned and key not in seen:
                seen.add(key)
                result.append(cleaned)
        return result
