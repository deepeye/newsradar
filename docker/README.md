# Docker 部署指南

## 快速启动

```bash
# 1. 创建环境变量文件
cp docker/.env.example .env

# 2. 编辑 .env 文件，填入 QWEN_API_KEY
vim .env

# 3. 启动所有服务
docker compose up -d

# 4. 查看服务状态
docker compose ps
```

## 服务列表

| 服务 | 端口 | 说明 |
|------|------|------|
| web | 3000 | Next.js 前端 |
| api | 8001 | FastAPI 后端 |
| collector | - | 爬虫服务 |
| postgres | 5432 | PostgreSQL 数据库 |
| redis | 6379 | Redis 缓存 |

## 单独启动服务

```bash
# 仅启动基础设施
docker compose up -d postgres redis

# 仅启动前端
docker compose up -d web

# 仅启动 API
docker compose up -d api

# 仅启动爬虫
docker compose up -d collector
```

## 停止服务

```bash
docker compose down

# 停止并删除数据卷
docker compose down -v
```

## 查看日志

```bash
# 所有服务日志
docker compose logs -f

# 单个服务日志
docker compose logs -f api
docker compose logs -f web
docker compose logs -f collector
```

## 重新构建

```bash
# 重新构建所有服务
docker compose build --no-cache

# 重新构建单个服务
docker compose build --no-cache api
```