import type { CSSProperties } from "react";
import type { MatchResult } from "../types";

const recommendationText: Record<MatchResult["recommendation"], string> = {
  strongly_recommended: "强烈推荐",
  recommended: "建议推进",
  consider: "谨慎考虑",
  not_recommended: "暂不推荐",
};

export function ScorePanel({ result }: { result: MatchResult }) {
  const scoreStyle = { "--score": `${result.score * 3.6}deg` } as CSSProperties;
  const job = result.job_requirements;
  const details = [
    ["技能匹配", result.score_details.skill_score],
    ["经验相关", result.score_details.experience_score],
    ["学历匹配", result.score_details.education_score],
    ["语义复核", result.score_details.semantic_score],
  ] as const;

  return (
    <section className="result-card score-card">
      <div className="score-hero">
        <div className="score-ring" style={scoreStyle} aria-label={`综合匹配度 ${result.score} 分`}>
          <div>
            <strong>{result.score}</strong>
            <span>/ 100</span>
          </div>
        </div>
        <div>
          <span className="eyebrow">综合匹配结论</span>
          <h2>{recommendationText[result.recommendation]}</h2>
          <p>{result.summary}</p>
          <span className="mode-badge">
            {result.scoring_mode === "ai_hybrid" ? "混合评分" : "确定性评分"}
          </span>
        </div>
      </div>

      <div className="requirements-panel">
        <div className="requirements-grid">
          <Requirement label="岗位名称" value={job.title || "未识别"} />
          <Requirement label="经验要求" value={job.minimum_years != null ? `${job.minimum_years} 年以上` : "未指定"} />
          <Requirement label="学历要求" value={job.minimum_degree || "未指定"} />
        </div>
        <div className="requirement-tags">
          <KeywordList title="必选技能" items={job.required_skills} positive />
          <KeywordList title="加分技能" items={job.preferred_skills} />
        </div>
        {job.responsibilities.length > 0 && (
          <div className="responsibility-list">
            <h3>职责摘要</h3>
            {job.responsibilities.slice(0, 3).map((item) => <p key={item}>{item}</p>)}
          </div>
        )}
      </div>

      <div className="metrics">
        {details.map(([label, value]) => (
          <div className="metric" key={label}>
            <div><span>{label}</span><strong>{value == null ? "—" : value}</strong></div>
            <div className="metric-track"><span style={{ width: `${value ?? 0}%` }} /></div>
          </div>
        ))}
      </div>

      <div className="keyword-columns">
        <KeywordList title="已匹配" items={result.matched_keywords} positive />
        <KeywordList title="待补充证据" items={result.missing_keywords} />
      </div>

      <div className="insight-columns">
        <InsightList title="优势" items={result.strengths} icon="+" />
        <InsightList title="风险与核验项" items={result.risks} icon="!" />
      </div>
    </section>
  );
}

function Requirement({ label, value }: { label: string; value: string }) {
  return (
    <div className="requirement-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function KeywordList({ title, items, positive = false }: { title: string; items: string[]; positive?: boolean }) {
  return (
    <div>
      <h3>{title}</h3>
      <div className="tags">
        {items.length ? items.map((item) => (
          <span className={`tag ${positive ? "tag-positive" : "tag-missing"}`} key={item}>{item}</span>
        )) : <span className="muted">无</span>}
      </div>
    </div>
  );
}

function InsightList({ title, items, icon }: { title: string; items: string[]; icon: string }) {
  return (
    <div className="insight-list">
      <h3>{title}</h3>
      {items.length ? items.map((item) => (
        <div className="insight" key={item}><span>{icon}</span><p>{item}</p></div>
      )) : <p className="muted">暂无</p>}
    </div>
  );
}
