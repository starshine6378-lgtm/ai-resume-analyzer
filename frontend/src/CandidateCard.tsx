import type { ResumeAnalysis } from "../types";

const empty = "未识别";

export function CandidateCard({ analysis }: { analysis: ResumeAnalysis }) {
  const candidate = analysis.candidate;
  const education = candidate.education[0];
  const projectEvidence = candidate.projects.slice(0, 3).map((project) => {
    const title = project.name || "项目经历";
    const tech = project.technologies.length ? ` · ${project.technologies.join("、")}` : "";
    return `${title}${tech}${project.description ? `：${project.description}` : ""}`;
  });

  return (
    <section className="result-card candidate-card">
      <div className="card-header">
        <div className="candidate-heading">
          <span className="candidate-avatar" aria-hidden="true">
            {(candidate.name || "候").trim().slice(0, 1)}
          </span>
          <div>
            <span className="eyebrow">候选人档案</span>
            <h2>{candidate.name || "姓名未识别"}</h2>
          </div>
        </div>
        <span className="mode-badge">
          {analysis.extraction_mode === "hybrid" ? "AI + 规则" : "规则模式"}
        </span>
      </div>

      <div className="profile-grid">
        <Info label="电话" value={candidate.phone || empty} />
        <Info label="邮箱" value={candidate.email || empty} />
        <Info label="所在地" value={candidate.address || empty} />
        <Info label="工作年限" value={candidate.years_of_experience != null ? `${candidate.years_of_experience} 年` : empty} />
        <Info label="求职意向" value={candidate.job_intention || empty} />
        <Info label="期望薪资" value={candidate.expected_salary || empty} />
        <Info label="最高学历" value={education?.degree || empty} />
        <Info label="院校 / 专业" value={[education?.school, education?.major].filter(Boolean).join(" · ") || empty} />
      </div>

      <div className="tag-section">
        <h3>技能画像</h3>
        <div className="tags">
          {candidate.skills.length ? candidate.skills.map((skill) => (
            <span className="tag" key={skill}>{skill}</span>
          )) : <span className="muted">没有识别到明确技能</span>}
        </div>
      </div>

      <div className="evidence-grid">
        <EvidenceList title="项目经历" items={projectEvidence} empty="未识别到项目经历" />
        <EvidenceList title="工作经历" items={candidate.work_experience.slice(0, 3)} empty="未识别到工作经历" />
      </div>

      <details className="text-preview">
        <summary>简历文本预览</summary>
        <p>{analysis.text_preview || "暂无文本预览"}</p>
      </details>

      <div className="document-meta">
        <span>{analysis.filename}</span>
        <span>{analysis.page_count} 页</span>
        <span>{analysis.cached ? "缓存命中" : "本次解析"}</span>
      </div>
    </section>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="info-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function EvidenceList({ title, items, empty }: { title: string; items: string[]; empty: string }) {
  return (
    <div className="evidence-block">
      <h3>{title}</h3>
      {items.length ? (
        items.map((item, index) => <p key={`${title}-${index}`}>{item}</p>)
      ) : (
        <p className="muted">{empty}</p>
      )}
    </div>
  );
}
