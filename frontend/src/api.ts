import type { AnalyzeAndMatchResponse, HealthResponse } from "./types";

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1"
).replace(/\/$/, "");

interface ApiErrorPayload {
  error?: {
    code?: string;
    message?: string;
    request_id?: string;
  };
}

export class ApiError extends Error {
  code: string;
  requestId?: string;

  constructor(message: string, code = "REQUEST_FAILED", requestId?: string) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.requestId = requestId;
  }
}

export async function analyzeAndMatch(
  file: File,
  jobDescription: string,
  useAiReview: boolean,
): Promise<AnalyzeAndMatchResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("job_description", jobDescription);
  form.append("use_ai_review", String(useAiReview));

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/analyze-and-match`, {
      method: "POST",
      body: form,
    });
  } catch {
    throw new ApiError("无法连接后端服务，请检查 API 地址或网络状态", "NETWORK_ERROR");
  }

  const payload = (await response.json().catch(() => ({}))) as
    | AnalyzeAndMatchResponse
    | ApiErrorPayload;

  if (!response.ok) {
    const errorPayload = payload as ApiErrorPayload;
    throw new ApiError(
      errorPayload.error?.message || `请求失败（${response.status}）`,
      errorPayload.error?.code,
      errorPayload.error?.request_id,
    );
  }

  return payload as AnalyzeAndMatchResponse;
}

export async function checkHealth(): Promise<HealthResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/health`);
  } catch {
    throw new ApiError("无法连接后端服务", "NETWORK_ERROR");
  }

  const payload = (await response.json().catch(() => ({}))) as HealthResponse | ApiErrorPayload;
  if (!response.ok) {
    const errorPayload = payload as ApiErrorPayload;
    throw new ApiError(
      errorPayload.error?.message || `健康检查失败（${response.status}）`,
      errorPayload.error?.code,
      errorPayload.error?.request_id,
    );
  }
  return payload as HealthResponse;
}
