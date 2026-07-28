# Talent Lens · AI 赋能的智能简历分析系统

Talent Lens 是一个面向招聘初筛场景的 Serverless MVP：上传单个 PDF 简历，自动解析多页文本，抽取候选人关键信息，并结合岗位描述生成可解释的匹配评分。

项目重点不是让大模型直接“拍脑袋给分”，而是把确定性规则、AI 结构化抽取、可解释评分和缓存组合起来：文件校验、联系方式识别、基础评分由程序兜底；非结构化信息、岗位语义和项目相关性由通义千问增强。

## 在线入口

提交前将下面地址替换为实际线上地址：

| 项目 | 地址 |
| --- | --- |
| GitHub 仓库 | `https://github.com/<your-name>/ai-resume-analyzer` |
| 前端演示 | `https://<your-name>.github.io/ai-resume-analyzer/` |
| 后端 Swagger | `https://<your-fc-domain>/docs` |
| 健康检查 | `https://<your-fc-domain>/api/v1/health` |

## 评审快速验收

1. 打开前端演示地址，确认右上角后端状态为“后端在线”。
2. 上传 [`samples/sample_resume.pdf`](samples/sample_resume.pdf)。
3. 使用页面内置示例岗位，点击“开始智能匹配”。
4. 查看返回结果：候选人档案、岗位需求拆解、综合评分、命中/缺失关键词、优势和风险。
5. 打开后端 Swagger，验证 `POST /api/v1/analyze-and-match`、`POST /api/v1/resumes/analyze`、`POST /api/v1/resumes/{resume_id}/match`。

## 需求覆盖

| 题目模块 | 实现情况 | 关键文件 |
| --- | --- | --- |
| 简历上传与解析 | 支持单个 PDF 上传、大小/签名校验、PyMuPDF 多页解析、文本清洗 | [`backend/app/api/routes.py`](backend/app/api/routes.py), [`backend/app/services/pdf_parser.py`](backend/app/services/pdf_parser.py), [`backend/app/services/text_cleaner.py`](backend/app/services/text_cleaner.py) |
| 关键信息提取 | 提取姓名、电话、邮箱、地址；扩展提取求职意向、薪资、工作年限、学历、技能、项目经历 | [`backend/app/services/fallback_extractor.py`](backend/app/services/fallback_extractor.py), [`backend/app/services/ai_service.py`](backend/app/services/ai_service.py) |
| 简历评分与匹配 | 拆解岗位技能、经验、学历要求，输出技能/经验/学历/语义四维评分 | [`backend/app/services/matching_service.py`](backend/app/services/matching_service.py) |
| 结果返回与缓存 | JSON 结构化返回，Redis 优先、内存 TTL 兜底；按 PDF/JD 哈希缓存 | [`backend/app/services/cache_service.py`](backend/app/services/cache_service.py), [`backend/app/services/orchestrator.py`](backend/app/services/orchestrator.py) |
| 前端页面 | React + Vite 工作台页面，支持上传、岗位编辑、状态检测、结果可视化，GitHub Pages 自动部署 | [`frontend/src/App.tsx`](frontend/src/App.tsx), [`frontend/src/components`](frontend/src/components), [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml) |

## 核心能力

- 单个 PDF 上传，校验扩展名、文件大小和 `%PDF` 签名
- PyMuPDF 解析多页文本，检测空文本/扫描版 PDF
- 清洗 Unicode、冗余空白、重复页眉页脚和段落
- 通义千问 OpenAI 兼容接口，使用 JSON Mode 做结构化抽取
- API Key 未配置或 AI 调用失败时自动降级到规则模式
- 岗位关键词、必选技能、加分技能、工作年限、学历要求解析
- 技能匹配率、工作经验相关性、学历匹配、AI 语义复核综合评分
- 输出命中关键词、缺失关键词、优势、风险、推荐等级和评分细节
- Redis 缓存可选；未配置 Redis 时使用进程内 TTL 缓存
- FastAPI Swagger、统一错误结构、Request ID、单元测试、CI
- React + Vite 响应式前端，支持 GitHub Pages 部署

## 技术架构

```text
React + Vite / GitHub Pages
            |
            | REST / multipart/form-data
            v
Alibaba Cloud Function Compute
FastAPI + PyMuPDF + Matching Engine
       |                    |
       v                    v
Qwen OpenAI-compatible API  Redis or in-memory TTL cache
```

```text
.
├── backend/
│   ├── app/
│   │   ├── api/            # REST 路由
│   │   ├── core/           # 配置、异常、日志和 CORS
│   │   ├── schemas/        # Pydantic 响应/请求模型
│   │   ├── services/       # PDF、清洗、AI、规则抽取、匹配、缓存
│   │   └── main.py
│   ├── tests/              # API、文本清洗、匹配算法测试
│   ├── Dockerfile
│   └── requirements*.txt
├── frontend/
│   ├── src/components/     # 上传、岗位描述、候选人卡、评分面板
│   └── src/
├── docs/                   # API 示例和 FC 部署说明
├── samples/                # 示例简历、岗位描述、响应数据
└── .github/workflows/      # CI 和 GitHub Pages 部署
```

## 本地运行

### 环境要求

- Python 3.10+，推荐 Python 3.11 或 3.12
- Node.js 20+
- npm 10+
- Redis 可选
- 通义千问 API Key 可选

不配置 `DASHSCOPE_API_KEY` 时，系统仍可完成 PDF 解析、规则抽取和确定性评分；配置后启用 AI 结构化抽取与语义复核。

### 后端

Windows PowerShell：

```powershell
conda create -n resume-analyzer python=3.11 -y
conda activate resume-analyzer

cd backend
Copy-Item .env.example .env
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload --port 8000
```

macOS / Linux：

```bash
cd backend
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload --port 8000
```

后端启动后打开：

- Swagger：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/api/v1/health`

### 前端

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

打开 `http://localhost:5173`。

本地 `.env.local` 示例：

```text
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### Docker Compose

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

Docker Compose 会启动后端和 Redis。后端地址为 `http://localhost:8000`，前端仍可通过 `frontend` 目录下的 `npm run dev` 启动。

## AI 配置

在 `backend/.env` 中填写：

```env
DASHSCOPE_API_KEY=sk-xxxxxxxx
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
```

项目通过 OpenAI 兼容 Chat Completions 接口调用通义千问，并设置：

```python
response_format={"type": "json_object"}
```

所有 AI Prompt 都要求只输出 JSON；后端再用 Pydantic 校验结构。模型超时、异常、返回空内容或非法 JSON 时，主流程自动降级，不影响基础解析和评分。

## REST API

### `GET /api/v1/health`

返回服务状态、环境、AI 是否启用、缓存后端。

### `POST /api/v1/resumes/analyze`

`multipart/form-data` 上传字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `file` | PDF file | 单个 PDF 简历 |

### `POST /api/v1/resumes/{resume_id}/match`

```json
{
  "job_description": "招聘 Python 后端工程师，要求 3 年经验，熟悉 FastAPI、MySQL、Redis 和 Docker。",
  "use_ai_review": true
}
```

### `POST /api/v1/analyze-and-match`

前端默认使用的一步式接口。表单字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `file` | PDF file | 单个 PDF 简历 |
| `job_description` | string | 岗位职责与任职要求 |
| `use_ai_review` | boolean | 是否启用 AI 语义复核 |

完整 curl 示例见 [`docs/API_EXAMPLES.md`](docs/API_EXAMPLES.md)。

## 评分设计

有 AI 语义复核时：

```text
总分 = 技能 50% + 工作经验 25% + 学历 10% + AI 语义 15%
```

无 AI 或 AI 调用失败时：

```text
总分 = 技能 60% + 工作经验 30% + 学历 10%
```

技能分内部：

- 必选技能：80%
- 加分技能：20%
- 岗位没有加分技能时，必选技能占 100%

推荐等级：

| 分数 | 等级 |
| --- | --- |
| `>= 80` | 强烈推荐 |
| `>= 65` | 建议推进 |
| `>= 50` | 谨慎考虑 |
| `< 50` | 暂不推荐 |

AI 语义评估明确禁止使用姓名、性别、年龄、婚育、民族、住址等与岗位胜任力无关的信息加减分。

## 缓存设计

```text
resume:parse:{pdf_sha256}:{prompt_version}
resume:id:{resume_id}
resume:match:{resume_id}:{jd_sha256}:{prompt_version}:ai-{0|1}
```

- PDF 内容哈希避免同名文件冲突
- JD 内容哈希避免重复评分
- Prompt 版本进入缓存 key，提取规则变更后旧缓存自动失效
- Redis 异常不会中断主流程
- 未配置 Redis 时使用进程内 TTL 缓存

函数计算可能横向扩容或冷启动。公开演示建议配置 Redis；如果只使用进程内缓存，分离的“解析后再匹配”请求可能落到不同实例。一步式 `/analyze-and-match` 不受该问题影响。

## 错误处理

统一错误响应：

```json
{
  "error": {
    "code": "PDF_TEXT_NOT_FOUND",
    "message": "未提取到足够文本；该文件可能是扫描版 PDF，请先进行 OCR",
    "request_id": "..."
  }
}
```

已覆盖非 PDF、空文件、文件超限、损坏/加密 PDF、扫描件、请求参数错误、缓存过期和内部异常。

## 测试与质量

```bash
cd backend
pytest -q
ruff check app tests

cd ../frontend
npm run build
```

测试覆盖文本清洗、技能别名、评分算法和完整 API 流程。GitHub Actions 会在 push 和 pull request 时运行后端测试、Ruff 检查和前端构建。

## 部署

### 后端部署到阿里云 FC

详细步骤见 [`docs/DEPLOY_FC.md`](docs/DEPLOY_FC.md)。推荐参数：

| 项目 | 值 |
| --- | --- |
| 代码目录 | `backend` |
| 启动命令 | `./start.sh` |
| 监听端口 | `9000` |
| Host | `0.0.0.0` |
| 内存 | `1024 MB` |
| 超时 | `60 秒` |

生产环境变量建议：

```text
ENVIRONMENT=production
CORS_ORIGINS=https://<your-name>.github.io
DASHSCOPE_API_KEY=<your-key>
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
REDIS_URL=redis://:<password>@<host>:6379/0
```

### 前端部署到 GitHub Pages

1. 在仓库 **Settings → Pages** 中将 Source 设为 **GitHub Actions**。
2. 在 **Settings → Secrets and variables → Actions → Variables** 添加：

```text
VITE_API_BASE_URL=https://<your-fc-domain>/api/v1
```

3. 推送到 `main`，工作流 [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml) 会构建并发布 `frontend/dist`。
4. 后端 `CORS_ORIGINS` 设置为你的 GitHub Pages Origin，例如 `https://<your-name>.github.io`。

## 隐私与安全

- 默认只在内存中处理文件，不落盘保存原始 PDF
- 缓存仅保存结构化结果和短文本预览，不保存 PDF 原文件
- API Key 只放在后端环境变量
- 限制文件大小和 PDF 签名
- 生产环境应配置精确 CORS 来源，不建议长期使用 `*`
- 公开演示建议增加 API 网关限流和日志脱敏

## 已知限制

- 纯扫描版 PDF 仅检测并提示，未内置 OCR
- 复杂双栏排版的文本顺序可能不完美
- 规则模式下的中文姓名、院校和项目结构提取能力有限
- 评分是招聘辅助信号，不应作为自动淘汰候选人的唯一依据

## 可继续扩展

- 阿里云 OCR 扫描件回退
- OSS 临时文件与生命周期清理
- Embedding 语义相似度与技能知识图谱
- 批量简历、异步任务和进度查询
- 招聘方登录、岗位管理和候选人排序
- Prompt/模型 A-B 测试和评分校准集

## 官方参考

- 阿里云函数计算 Web/FastAPI 部署文档：`https://help.aliyun.com/en/functioncompute/`
- 阿里云百炼 OpenAI 兼容接口：`https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions`
- 千问结构化输出：`https://help.aliyun.com/en/model-studio/qwen-structured-output`
- GitHub Pages 自定义 Actions：`https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site`

## License

MIT
