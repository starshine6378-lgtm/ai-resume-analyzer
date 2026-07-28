import logging

from app.core.config import Settings
from app.core.errors import AppError
from app.schemas.api import MatchResponse, ResumeAnalysisResponse
from app.schemas.job import MatchRequest
from app.schemas.resume import CandidateProfile
from app.services.ai_service import AIService
from app.services.cache_service import CacheService
from app.services.fallback_extractor import extract_candidate_rules, extract_job_rules
from app.services.matching_service import build_match_response
from app.services.pdf_parser import extract_pdf_text
from app.services.text_cleaner import clean_resume_text
from app.utils.hashing import sha256_bytes, sha256_text

logger = logging.getLogger(__name__)


class ResumeOrchestrator:
    def __init__(self, settings: Settings, cache: CacheService) -> None:
        self.settings = settings
        self.cache = cache
        self.ai = AIService(settings)

    @staticmethod
    def _merge_profiles(ai_profile: CandidateProfile, rules: CandidateProfile) -> CandidateProfile:
        data = ai_profile.model_dump()
        for field in (
            "name",
            "phone",
            "email",
            "address",
            "job_intention",
            "expected_salary",
            "years_of_experience",
        ):
            if not data.get(field):
                data[field] = getattr(rules, field)

        data["skills"] = list(dict.fromkeys([*ai_profile.skills, *rules.skills]))
        if not data.get("education"):
            data["education"] = [item.model_dump() for item in rules.education]
        if not data.get("projects"):
            data["projects"] = [item.model_dump() for item in rules.projects]
        if not data.get("work_experience"):
            data["work_experience"] = rules.work_experience
        return CandidateProfile.model_validate(data)

    async def analyze_pdf(self, filename: str, content: bytes) -> ResumeAnalysisResponse:
        full_hash = sha256_bytes(content)
        resume_id = full_hash[:24]
        parse_key = f"resume:parse:{full_hash}:{self.settings.prompt_version}"
        resume_key = f"resume:id:{resume_id}"

        cached = await self.cache.get_json(parse_key)
        if cached:
            response = ResumeAnalysisResponse.model_validate({**cached, "cached": True})
            await self.cache.set_json(
                resume_key,
                response.model_dump(mode="json"),
                self.settings.resume_cache_ttl_seconds,
            )
            return response

        parsed = extract_pdf_text(content)
        cleaned_text = clean_resume_text(parsed.text)
        rule_profile = extract_candidate_rules(cleaned_text)
        profile = rule_profile
        warnings: list[str] = []
        extraction_mode: str = "rules"

        if self.ai.enabled:
            try:
                ai_profile = await self.ai.extract_candidate(cleaned_text)
                profile = self._merge_profiles(ai_profile, rule_profile)
                extraction_mode = "hybrid"
            except Exception as exc:
                logger.exception("AI resume extraction failed")
                warnings.append(f"AI 提取失败，已使用规则模式降级：{type(exc).__name__}")
        else:
            warnings.append("未配置 DASHSCOPE_API_KEY，当前使用规则提取模式")

        response = ResumeAnalysisResponse(
            resume_id=resume_id,
            cached=False,
            filename=filename,
            page_count=parsed.page_count,
            raw_text_length=len(cleaned_text),
            extraction_mode=extraction_mode,  # type: ignore[arg-type]
            candidate=profile,
            text_preview=cleaned_text[:1000],
            warnings=warnings,
        )
        payload = response.model_dump(mode="json")
        await self.cache.set_json(parse_key, payload, self.settings.resume_cache_ttl_seconds)
        await self.cache.set_json(resume_key, payload, self.settings.resume_cache_ttl_seconds)
        return response

    async def get_analysis(self, resume_id: str) -> ResumeAnalysisResponse:
        cached = await self.cache.get_json(f"resume:id:{resume_id}")
        if not cached:
            raise AppError(
                "RESUME_NOT_FOUND",
                "未找到该简历，缓存可能已过期，请重新上传",
                404,
            )
        return ResumeAnalysisResponse.model_validate({**cached, "cached": True})

    async def match_resume(self, resume_id: str, request: MatchRequest) -> MatchResponse:
        analysis = await self.get_analysis(resume_id)
        job_hash = sha256_text(request.job_description.strip())
        match_key = (
            f"resume:match:{resume_id}:{job_hash}:{self.settings.prompt_version}:"
            f"ai-{int(request.use_ai_review)}"
        )
        cached = await self.cache.get_json(match_key)
        if cached:
            return MatchResponse.model_validate({**cached, "cached": True})

        job = extract_job_rules(request.job_description)
        if self.ai.enabled:
            try:
                job = await self.ai.extract_job(request.job_description)
            except Exception:
                logger.exception("AI job extraction failed; using rules")

        semantic_review = None
        if self.ai.enabled and request.use_ai_review:
            try:
                semantic_review = await self.ai.semantic_review(analysis.candidate, job)
            except Exception:
                logger.exception("AI semantic review failed; using deterministic score")

        response = build_match_response(
            resume_id=resume_id,
            candidate=analysis.candidate,
            job=job,
            semantic_review=semantic_review,
        )
        await self.cache.set_json(
            match_key,
            response.model_dump(mode="json"),
            self.settings.match_cache_ttl_seconds,
        )
        return response
