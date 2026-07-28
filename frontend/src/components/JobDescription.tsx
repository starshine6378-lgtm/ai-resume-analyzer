import type { ChangeEvent } from "react";

interface Props {
  value: string;
  onChange: (value: string) => void;
  useAiReview: boolean;
  onAiReviewChange: (value: boolean) => void;
  onUseExample: () => void;
  onClear: () => void;
  disabled?: boolean;
}

export function JobDescription({
  value,
  onChange,
  useAiReview,
  onAiReviewChange,
  onUseExample,
  onClear,
  disabled,
}: Props) {
  return (
    <section className="panel" aria-labelledby="jd-title">
      <div className="section-heading">
        <span className="step">02</span>
        <div>
          <h2 id="jd-title">岗位需求</h2>
          <p>系统会区分必选技能、加分技能、经验与学历要求。</p>
        </div>
        <div className="panel-actions">
          <button type="button" className="ghost-button" onClick={onUseExample} disabled={disabled}>
            示例岗位
          </button>
          <button type="button" className="ghost-button" onClick={onClear} disabled={disabled || !value}>
            清空
          </button>
        </div>
      </div>

      <label className="sr-only" htmlFor="job-description">岗位描述</label>
      <textarea
        id="job-description"
        value={value}
        disabled={disabled}
        onChange={(event: ChangeEvent<HTMLTextAreaElement>) => onChange(event.target.value)}
        placeholder="粘贴岗位职责与任职要求……"
        rows={12}
      />
      <div className="textarea-meta">
        <span>{value.length} 字</span>
        <label className="switch-row" aria-label="启用 AI 语义复核">
          <input
            type="checkbox"
            checked={useAiReview}
            disabled={disabled}
            onChange={(event: ChangeEvent<HTMLInputElement>) => onAiReviewChange(event.target.checked)}
          />
          <span>{useAiReview ? "AI 语义复核开启" : "确定性评分"}</span>
        </label>
      </div>
    </section>
  );
}
