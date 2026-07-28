# API 调用示例

## 健康检查

```bash
curl http://localhost:8000/api/v1/health
```

## 上传并解析

```bash
curl -X POST http://localhost:8000/api/v1/resumes/analyze \
  -F "file=@./resume.pdf"
```

## 使用已解析简历匹配岗位

```bash
curl -X POST http://localhost:8000/api/v1/resumes/<resume_id>/match \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "招聘 Python 后端工程师，要求 3 年经验，熟悉 FastAPI、MySQL、Redis 和 Docker。",
    "use_ai_review": true
  }'
```

## 一步完成解析和匹配

```bash
curl -X POST http://localhost:8000/api/v1/analyze-and-match \
  -F "file=@./resume.pdf" \
  -F "job_description=招聘 Python 后端工程师，要求 3 年经验，熟悉 FastAPI、MySQL、Redis 和 Docker。" \
  -F "use_ai_review=true"
```
