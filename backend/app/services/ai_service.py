import asyncio
import json
import logging
from typing import Any, TypeVar

try:
    from openai import AsyncOpenAI
except ImportError:  # Optional until DASHSCOPE_API_KEY is configured.
    AsyncOpenAI = None  # type: ignore[assignment,misc]

from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.schemas.job import JobRequirements, SemanticReview
from app.schemas.resume import CandidateProfile

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

RESUME_SYSTEM_PROMPT = """
你是专业的招聘简历信息抽取服务。把输入简历转换为严格 JSON 对象。
规则：
1. 不得编造，未知单值字段用 null，未知数组用 []。
2. JSON 字段必须为：name, phone, email, address, job_intention,
   expected_salary, years_of_experience, education, skills, projects, work_experience。
3. education 元素字段：school, degree, major, start_date, end_date。
4. projects 元素字段：name, description, technologies。
5. 技能名规范化，例如 Python、FastAPI、Redis、Docker、Kubernetes。
6. years_of_experience 是数字；无法可靠判断则为 null。
7. 只输出 JSON，不要 Markdown，不要解释。
""".strip()

JOB_SYSTEM_PROMPT = """
你是招聘岗位需求分析服务。把岗位描述转换为严格 JSON 对象。
字段：title, required_skills, preferred_skills, minimum_years,
minimum_degree, responsibilities。
“必须/要求/熟悉/精通”归 required_skills；“优先/加分/更佳”归 preferred_skills。
不编造，未知单值用 null，未知数组用 []。只输出 JSON。
""".strip()

SEMANTIC_SYSTEM_PROMPT = """
你是谨慎、可解释的招聘匹配评审服务。根据候选人结构化资料和岗位要求，
评估项目、职责和技术使用场景的相关性。只返回 JSON：
{"semantic_score": 0-100, "strengths": [], "risks": [], "summary": ""}。
不得因姓名、性别、年龄、婚育、民族、住址等与胜任力无关的信息加减分。
证据不足时降低置信度并在 risks 中说明。只输出 JSON。
""".strip()


class AIService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.enabled = settings.ai_enabled and AsyncOpenAI is not None
        if settings.ai_enabled and AsyncOpenAI is None:
            logger.warning("DASHSCOPE_API_KEY is configured but the openai package is unavailable")
        self.client = (
            AsyncOpenAI(
                api_key=settings.dashscope_api_key.get_secret_value(),  # type: ignore[union-attr]
                base_url=settings.dashscope_base_url,
                timeout=settings.ai_timeout_seconds,
            )
            if self.enabled
            else None
        )

    async def _json_completion(
        self,
        system_prompt: str,
        user_content: str,
        output_model: type[T],
    ) -> T:
        if not self.client:
            raise RuntimeError("AI service is disabled")

        attempts = max(1, self.settings.ai_max_retries)
        last_error: Exception | None = None
        for attempt_index in range(attempts):
            try:
                response = await self.client.chat.completions.create(
                    model=self.settings.qwen_model,
                    temperature=0,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                )
                content = response.choices[0].message.content
                if not content:
                    raise ValueError("模型返回为空")
                try:
                    payload: Any = json.loads(content)
                    return output_model.model_validate(payload)
                except (json.JSONDecodeError, ValidationError) as exc:
                    logger.warning("Invalid AI JSON: %s", content[:500])
                    raise ValueError("模型返回的 JSON 不符合结构") from exc
            except Exception as exc:
                last_error = exc
                if attempt_index + 1 < attempts:
                    await asyncio.sleep(min(0.5 * (2**attempt_index), 3.0))

        raise RuntimeError("AI request failed") from last_error

    async def extract_candidate(self, resume_text: str) -> CandidateProfile:
        content = resume_text[: self.settings.max_resume_chars]
        return await self._json_completion(
            RESUME_SYSTEM_PROMPT,
            f"请提取以下简历并输出 JSON：\n\n{content}",
            CandidateProfile,
        )

    async def extract_job(self, job_description: str) -> JobRequirements:
        return await self._json_completion(
            JOB_SYSTEM_PROMPT,
            f"请分析以下岗位描述并输出 JSON：\n\n{job_description}",
            JobRequirements,
        )

    async def semantic_review(
        self,
        candidate: CandidateProfile,
        job: JobRequirements,
    ) -> SemanticReview:
        payload = {
            "candidate": candidate.model_dump(mode="json"),
            "job_requirements": job.model_dump(mode="json"),
        }
        return await self._json_completion(
            SEMANTIC_SYSTEM_PROMPT,
            "请基于以下数据评审并输出 JSON：\n" + json.dumps(payload, ensure_ascii=False),
            SemanticReview,
        )
