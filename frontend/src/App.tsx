import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { API_BASE_URL, analyzeAndMatch, ApiError, checkHealth } from "./api";
import { CandidateCard } from "./components/CandidateCard";
import { JobDescription } from "./components/JobDescription";
import { ResumeUpload } from "./components/ResumeUpload";
import { ScorePanel } from "./components/ScorePanel";
import type { AnalyzeAndMatchResponse } from "./types";

const DEFAULT_JOB = `Python 后端开发工程师
岗位职责：
1. 负责招聘业务后端服务的设计、开发和性能优化；
2. 参与 RESTful API、缓存及异步任务模块建设；
3. 与前端和产品协作交付稳定的业务能力。

任职要求：
1. 本科及以上学历，3 年以上 Python 后端开发经验；
2. 熟悉 Python、FastAPI、MySQL、Redis 和 Docker；
3. 熟悉 Linux、Git，具备良好的接口设计能力；
4. 有微服务、Kubernetes 或 Serverless 项目经验者优先。`;

const FLOW_STEPS = [
  ["PDF 校验", "类型、签名、大小"],
  ["文本解析", "PyMuPDF 多页提取"],
  ["信息抽取", "规则兜底 + Qwen 增强"],
  ["岗位匹配", "技能、经验、学历、语义"],
  ["JSON 返回", "可解释评分与缓存"],
] as const;

type ApiState = "checking" | "online" | "offline";

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState(DEFAULT_JOB);
  const [useAiReview, setUseAiReview] = useState(true);
  const [result, setResult] = useState<AnalyzeAndMatchResponse | null>(null);
  const [error, setError] = useState("");
  const [requestId, setRequestId] = useState("");
  const [loading, setLoading] = useState(false);
  const [apiState, setApiState] = useState<ApiState>("checking");
  const [apiDetail, setApiDetail] = useState("正在检测后端服务");

  useEffect(() => {
    let active = true;
    checkHealth()
      .then((health) => {
        if (!active) return;
        setApiState("online");
        setApiDetail(
          `${health.environment} · ${health.ai_enabled ? "AI 已启用" : "规则模式"} · ${health.cache_backend}`,
        );
      })
      .catch(() => {
        if (!active) return;
        setApiState("offline");
        setApiDetail("未连接，可先检查 VITE_API_BASE_URL 或本地后端");
      });
    return () => {
      active = false;
    };
  }, []);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setRequestId("");
    if (!file) {
      setError("请先选择一份 PDF 简历");
      return;
    }
    if (jobDescription.trim().length < 20) {
      setError("岗位描述至少需要 20 个字符");
      return;
    }

    setLoading(true);
    try {
      const response = await analyzeAndMatch(file, jobDescription.trim(), useAiReview);
      setResult(response);
      window.setTimeout(() => document.getElementById("results")?.scrollIntoView({ behavior: "smooth" }), 50);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
        setRequestId(caught.requestId || "");
      } else {
        setError("分析失败，请稍后重试");
      }
    } finally {
      setLoading(false);
    }
  };

  const jobLength = jobDescription.trim().length;
  const ready = Boolean(file && jobLength >= 20 && !loading);

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="Talent Lens 首页">
          <span className="brand-mark">TL</span>
          <span>
            <strong>TalentLens</strong>
            <small>AI 招聘决策助手</small>
          </span>
        </a>
        <div className="topbar-actions">
          <a
            className="api-link"
            href={`${API_BASE_URL}/health`}
            target="_blank"
            rel="noreferrer"
            title={API_BASE_URL}
          >
            API 状态
          </a>
          <a
            className="repo-link"
            href="https://github.com/starshine6378-lgtm/ai-resume-analyzer"
            target="_blank"
            rel="noreferrer"
          >
            GitHub
          </a>
          <StatusChip state={apiState} label={apiState === "online" ? "后端在线" : apiState === "offline" ? "后端未连接" : "检测中"} />
        </div>
      </header>

      <main id="top">
        <section className="console-hero">
          <div className="hero-copy">
            <span className="eyebrow">AI RECRUITING · SERVERLESS</span>
            <h1>AI 智能简历分析</h1>
            <p>把 PDF 简历转成结构化候选人档案，并结合岗位要求生成清晰、可追溯的匹配结论。</p>
            <div className="hero-metrics" aria-label="核心能力">
              <HeroMetric value="PDF" label="多页解析" />
              <HeroMetric value="Qwen" label="信息抽取" />
              <HeroMetric value="Redis" label="缓存优先" />
              <HeroMetric value="FC" label="弹性部署" />
            </div>
          </div>

          <aside className="review-brief" aria-label="评审路径">
            <div className="brief-header">
              <div>
                <span className="eyebrow">PROCESS</span>
                <h2>一次请求的处理链路</h2>
              </div>
              <strong>5 步</strong>
            </div>
            <ol className="flow-list">
              {FLOW_STEPS.map(([title, detail], index) => (
                <li key={title}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <div>
                    <strong>{title}</strong>
                    <small>{detail}</small>
                  </div>
                </li>
              ))}
            </ol>
          </aside>
        </section>

        <form onSubmit={submit} className="workspace">
          <div className="input-stack">
            <ResumeUpload file={file} onChange={setFile} disabled={loading} />
            <JobDescription
              value={jobDescription}
              onChange={setJobDescription}
              useAiReview={useAiReview}
              onAiReviewChange={setUseAiReview}
              onUseExample={() => setJobDescription(DEFAULT_JOB)}
              onClear={() => setJobDescription("")}
              disabled={loading}
            />
          </div>

          <aside className="run-panel">
            <div className="run-panel-header">
              <span className="eyebrow">ANALYSIS RUN</span>
              <h2>提交分析任务</h2>
              <p>{apiDetail}</p>
            </div>

            <div className="run-list">
              <RunItem label="简历文件" value={file ? file.name : "等待上传"} detail={file ? formatFileSize(file.size) : "PDF · 单文件"} />
              <RunItem label="岗位描述" value={`${jobLength} 字`} detail={jobLength >= 20 ? "可提交" : "至少 20 字"} />
              <RunItem label="评分模式" value={useAiReview ? "AI 语义复核" : "确定性评分"} detail="失败自动降级" />
              <RunItem label="结果输出" value="JSON + 可解释视图" detail={result ? "已有分析结果" : "待生成"} />
            </div>

            <button className="primary-button" type="submit" disabled={!ready}>
              {loading ? (
                <>
                  <span className="spinner" /> 正在分析
                </>
              ) : (
                <>
                  开始智能匹配 <span className="button-arrow" aria-hidden="true">→</span>
                </>
              )}
            </button>

            {error && (
              <div className="error-banner" role="alert">
                <strong>分析未完成</strong>
                <span>{error}{requestId ? ` · Request ID: ${requestId}` : ""}</span>
              </div>
            )}
          </aside>
        </form>

        {result && (
          <section className="results" id="results">
            <div className="results-heading">
              <div>
                <span className="eyebrow">ANALYSIS REPORT</span>
                <h2>候选人匹配报告</h2>
                <p>分数用于辅助筛选，建议结合面试、作品和业务场景复核。</p>
              </div>
              <div className="result-stats" aria-label="结果概览">
                <ResultStat label="综合分" value={`${result.match.score}`} />
                <ResultStat label="推荐" value={recommendationText(result.match.recommendation)} />
                <ResultStat label="缓存" value={result.match.cached || result.analysis.cached ? "命中" : "未命中"} />
              </div>
            </div>

            {result.analysis.warnings.length > 0 && (
              <div className="warning-banner">{result.analysis.warnings.join("；")}</div>
            )}

            <div className="result-grid">
              <CandidateCard analysis={result.analysis} />
              <ScorePanel result={result.match} />
            </div>
          </section>
        )}
      </main>

      <footer>
        <span>Talent Lens · 面试作业演示项目</span>
        <span>默认不持久化原始 PDF</span>
      </footer>
    </div>
  );
}

function StatusChip({ state, label }: { state: ApiState; label: string }) {
  return (
    <span className={`status-chip is-${state}`}>
      <i aria-hidden="true" />
      {label}
    </span>
  );
}

function HeroMetric({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function RunItem({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="run-item">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

function ResultStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatFileSize(size: number) {
  return `${(size / 1024 / 1024).toFixed(2)} MB`;
}

function recommendationText(value: AnalyzeAndMatchResponse["match"]["recommendation"]) {
  const map: Record<AnalyzeAndMatchResponse["match"]["recommendation"], string> = {
    strongly_recommended: "强烈推荐",
    recommended: "建议推进",
    consider: "谨慎考虑",
    not_recommended: "暂不推荐",
  };
  return map[value];
}
