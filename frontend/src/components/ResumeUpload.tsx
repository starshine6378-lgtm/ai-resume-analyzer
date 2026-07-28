import { useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";

interface Props {
  file: File | null;
  onChange: (file: File | null) => void;
  disabled?: boolean;
}

const MAX_SIZE = 10 * 1024 * 1024;

export function ResumeUpload({ file, onChange, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragging, setDragging] = useState(false);
  const [localError, setLocalError] = useState("");

  const acceptFile = (nextFile?: File) => {
    setLocalError("");
    if (!nextFile) return;
    if (!nextFile.name.toLowerCase().endsWith(".pdf")) {
      setLocalError("请选择 PDF 文件");
      return;
    }
    if (nextFile.size > MAX_SIZE) {
      setLocalError("文件不能超过 10 MB");
      return;
    }
    onChange(nextFile);
  };

  return (
    <section className="panel upload-panel" aria-labelledby="resume-title">
      <div className="section-heading">
        <span className="step">01</span>
        <div>
          <h2 id="resume-title">上传简历</h2>
          <p>仅处理单个 PDF，后端按内容哈希生成简历 ID。</p>
        </div>
      </div>

      <button
        type="button"
        className={`drop-zone ${dragging ? "is-dragging" : ""} ${file ? "has-file" : ""}`}
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        onDragOver={(event: DragEvent<HTMLButtonElement>) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event: DragEvent<HTMLButtonElement>) => {
          event.preventDefault();
          setDragging(false);
          acceptFile(event.dataTransfer.files[0]);
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          hidden
          onChange={(event: ChangeEvent<HTMLInputElement>) => acceptFile(event.target.files?.[0])}
        />
        <span className="upload-icon" aria-hidden="true">PDF</span>
        {file ? (
          <>
            <strong>{file.name}</strong>
            <span>{(file.size / 1024 / 1024).toFixed(2)} MB · 点击重新选择</span>
          </>
        ) : (
          <>
            <strong>拖入 PDF，或点击选择</strong>
            <span>最大 10 MB，支持多页文本型 PDF</span>
          </>
        )}
      </button>

      <div className="upload-meta" aria-label="上传约束">
        <span>单文件</span>
        <span>PDF 签名校验</span>
        <span>最大 10 MB</span>
      </div>

      {file && (
        <button className="text-button" type="button" onClick={() => onChange(null)} disabled={disabled}>
          移除文件
        </button>
      )}
      {localError && <p className="field-error">{localError}</p>}
    </section>
  );
}
