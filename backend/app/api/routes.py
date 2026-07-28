from functools import lru_cache

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.schemas.api import (
    AnalyzeAndMatchResponse,
    HealthResponse,
    MatchResponse,
    ResumeAnalysisResponse,
)
from app.schemas.job import MatchRequest
from app.services.cache_service import CacheService, get_cache_service
from app.services.orchestrator import ResumeOrchestrator

router = APIRouter()


@lru_cache
def _orchestrator() -> ResumeOrchestrator:
    return ResumeOrchestrator(get_settings(), get_cache_service())


def get_orchestrator() -> ResumeOrchestrator:
    return _orchestrator()


async def _read_valid_pdf(file: UploadFile, settings: Settings) -> tuple[str, bytes]:
    filename = (file.filename or "resume.pdf").strip()
    if not filename.lower().endswith(".pdf"):
        raise AppError("UNSUPPORTED_FILE_TYPE", "仅支持单个 PDF 文件", 400)

    content = await file.read(settings.max_pdf_size_bytes + 1)
    await file.close()
    if not content:
        raise AppError("EMPTY_FILE", "上传文件为空", 400)
    if len(content) > settings.max_pdf_size_bytes:
        raise AppError(
            "FILE_TOO_LARGE",
            f"PDF 文件不能超过 {settings.max_pdf_size_mb} MB",
            413,
        )
    if not content.startswith(b"%PDF"):
        raise AppError("INVALID_PDF_SIGNATURE", "文件内容不是有效 PDF", 400)
    return filename, content


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health(
    settings: Settings = Depends(get_settings),
    cache: CacheService = Depends(get_cache_service),
) -> HealthResponse:
    return HealthResponse(
        service=settings.app_name,
        environment=settings.environment,
        ai_enabled=settings.ai_enabled,
        cache_backend=cache.backend_name,
    )


@router.post(
    "/resumes/analyze",
    response_model=ResumeAnalysisResponse,
    tags=["Resumes"],
)
async def analyze_resume(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    orchestrator: ResumeOrchestrator = Depends(get_orchestrator),
) -> ResumeAnalysisResponse:
    filename, content = await _read_valid_pdf(file, settings)
    return await orchestrator.analyze_pdf(filename, content)


@router.get(
    "/resumes/{resume_id}",
    response_model=ResumeAnalysisResponse,
    tags=["Resumes"],
)
async def get_resume(
    resume_id: str,
    orchestrator: ResumeOrchestrator = Depends(get_orchestrator),
) -> ResumeAnalysisResponse:
    return await orchestrator.get_analysis(resume_id)


@router.post(
    "/resumes/{resume_id}/match",
    response_model=MatchResponse,
    tags=["Matching"],
)
async def match_resume(
    resume_id: str,
    request: MatchRequest,
    orchestrator: ResumeOrchestrator = Depends(get_orchestrator),
) -> MatchResponse:
    return await orchestrator.match_resume(resume_id, request)


@router.post(
    "/analyze-and-match",
    response_model=AnalyzeAndMatchResponse,
    tags=["Demo"],
)
async def analyze_and_match(
    file: UploadFile = File(...),
    job_description: str = Form(..., min_length=20, max_length=20_000),
    use_ai_review: bool = Form(True),
    settings: Settings = Depends(get_settings),
    orchestrator: ResumeOrchestrator = Depends(get_orchestrator),
) -> AnalyzeAndMatchResponse:
    filename, content = await _read_valid_pdf(file, settings)
    analysis = await orchestrator.analyze_pdf(filename, content)
    match = await orchestrator.match_resume(
        analysis.resume_id,
        MatchRequest(job_description=job_description, use_ai_review=use_ai_review),
    )
    return AnalyzeAndMatchResponse(analysis=analysis, match=match)
