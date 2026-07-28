# 部署到阿里云函数计算 FC

推荐采用 **Function Compute 的 Web Service 仓库部署方式**，它能直接运行 FastAPI 项目。

## 控制台部署参数

- 代码目录：`backend`
- 运行时/构建环境：Python 3.12（或控制台当前提供的兼容版本）
- 安装命令：`pip install -r requirements.txt -t .`
- 启动命令：`./start.sh`
- 监听端口：`9000`
- 内存：1024 MB
- 超时：60 秒
- 磁盘：512 MB
- 健康检查：`/api/v1/health`

`start.sh` 会监听 `0.0.0.0:${PORT:-9000}`。如果控制台选择其他端口，同时设置 `PORT` 环境变量和监听端口即可。

部署完成后，Swagger 地址通常为：

```text
https://<your-fc-domain>/docs
```

## 环境变量

至少设置：

```text
ENVIRONMENT=production
CORS_ORIGINS=https://<username>.github.io
DASHSCOPE_API_KEY=<your-key>
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
```

可选 Redis：

```text
REDIS_URL=redis://:<password>@<host>:6379/0
```

## Docker 镜像方式

项目内的 `backend/Dockerfile` 可用于 FC Custom Container：

```bash
docker build -t ai-resume-analyzer ./backend
docker run --rm -p 9000:9000 --env-file backend/.env ai-resume-analyzer
```

在 FC 自定义容器中把 `CAPort/监听端口` 设置为 `9000`。

## 线上检查

```bash
curl https://<your-fc-domain>/api/v1/health
```

然后把该域名写入 GitHub 仓库变量：

```text
VITE_API_BASE_URL=https://<your-fc-domain>/api/v1
```

前端部署到 GitHub Pages 后，记得把后端 `CORS_ORIGINS` 改为 Pages 的 Origin，例如：

```text
CORS_ORIGINS=https://<username>.github.io
```
