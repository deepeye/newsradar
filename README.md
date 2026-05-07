# NewsRadar

A newsroom intelligence platform for monitoring trending topics, managing editorial workflows, and leveraging AI-powered content creation.

[中文](#概述) | [English](#overview)

---

## 概述

NewsRadar 是一个面向新闻编辑室的智能情报平台，集热点监控、AI 内容发现、选题大纲管理、文章工作台和 KOL 追踪于一体，帮助编辑团队高效捕捉热点、规划选题、完成创作。

## Overview

NewsRadar is an intelligence platform designed for newsrooms. It integrates trending topic monitoring, AI-powered content discovery, editorial outline management, article workbench, and KOL tracking to help editorial teams efficiently capture hot topics, plan stories, and complete content creation.

---

## 功能模块 / Features

| 模块 / Module | 说明 / Description |
|---|---|
| **Dashboard** | 实时热点监控面板，聚合多平台热门内容，展示趋势卡片与 AI 选题建议 |
| **AI Discovery** | 基于组织定位与编辑方针，AI 智能发现匹配的新闻选题与角度 |
| **Outlines** | 选题大纲管理，支持 AI 生成大纲、编辑、分类和状态跟踪 |
| **Workbench** | 文章工作台，支持 AI 辅助撰写、段落续写、质量评分与实时预览 |
| **KOL** | KOL（关键意见领袖）追踪，支持微博、X(Twitter) 等平台账号监控与内容采集 |
| **Data Sources** | 动态数据源管理，支持 RSS、API、网页抓取等多种采集方式 |

---

## 技术栈 / Tech Stack

### 前端 / Frontend
- **Next.js** 16.2 + **React** 19.2 + **TypeScript** 5
- **Tailwind CSS** v4 + **shadcn** UI 组件库
- **TanStack Query** 数据获取与缓存
- **Zustand** 状态管理

### API 服务 / Backend
- **FastAPI** + **Uvicorn** — 高性能异步 Web 框架
- **SQLAlchemy** 2.0 + **asyncpg** — 异步 ORM 与 PostgreSQL 驱动
- **Alembic** — 数据库迁移管理
- **Pydantic** + **Pydantic-Settings** — 数据校验与配置管理
- **python-jose** + **passlib** — JWT 认证与密码哈希

### 采集服务 / Collector
- **Scrapling** + **Playwright** — 高性能网页抓取与浏览器自动化
- **APScheduler** — 定时任务调度
- **curl_cffi** — 模拟真实浏览器指纹的 HTTP 请求

### 基础设施 / Infrastructure
- **PostgreSQL** 15 — 主数据库
- **Redis** 7 — 缓存与任务队列
- **Nginx** — 反向代理与静态资源缓存
- **Docker** + **Docker Compose** — 容器化部署

### AI 能力 / AI
- **Qwen (通义千问)** — 内容分析、选题建议、大纲生成、文章撰写与翻译

---

## 项目结构 / Project Structure

```
newsradar/
├── web/                    # 前端 Next.js 应用
│   ├── src/app/            # App Router 页面
│   ├── src/components/     # React 组件
│   ├── src/lib/            # 工具库、API 客户端、类型定义
│   └── Dockerfile
├── api/                    # FastAPI 后端服务
│   ├── app/api/            # API 路由
│   ├── app/models/         # SQLAlchemy 数据模型
│   ├── app/repositories/   # 数据访问层
│   ├── app/schemas/        # Pydantic 数据校验
│   ├── app/services/       # 业务逻辑层
│   ├── migrations/         # Alembic 数据库迁移
│   └── Dockerfile
├── clue-collector/         # 数据采集服务
│   ├── app/collectors/     # 采集器实现
│   ├── app/scheduler/      # 任务调度
│   ├── app/storage/        # 数据存储模型
│   ├── migrations/         # 数据库迁移
│   └── Dockerfile
├── docker/                 # Docker Compose 与 Nginx 配置
│   ├── docker-compose.yml
│   └── nginx.conf
└── bruno/                  # Bruno API 测试集合
```

---

## 快速开始 / Quick Start

### 环境要求 / Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- (可选) Node.js 22+ — 本地前端开发
- (可选) Python 3.12+ — 本地后端开发

### 使用 Docker Compose 部署 / Deploy with Docker Compose

1. **克隆仓库 / Clone the repository**

```bash
git clone https://github.com/deepeye/newsradar.git
cd newsradar/docker
```

2. **配置环境变量 / Configure environment**

创建 `.env` 文件：

```bash
cat > .env << 'EOF'
# JWT Secret (change in production)
JWT_SECRET_KEY=your-secret-key-change-me

# Qwen AI API Key (required for AI features)
QWEN_API_KEY=your-qwen-api-key
QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1

# Translation settings
TRANSLATION_ENABLED=true
TRANSLATION_THINKING_ENABLED=false

# Proxy (optional)
HTTP_PROXY=http://host.docker.internal:7897
HTTPS_PROXY=http://host.docker.internal:7897

# Log level
LOG_LEVEL=INFO
EOF
```

3. **启动服务 / Start services**

```bash
docker compose up -d
```

4. **访问 / Access**

- Web UI: http://localhost:8084
- API: http://localhost:8084/newsradar/api/
- API Docs: http://localhost:8001/docs (direct access)

5. **初始化数据库 / Initialize database**

```bash
# API 数据库迁移
docker exec newsradar-api alembic upgrade head

# Collector 数据库迁移
docker exec newsradar-collector alembic upgrade head
```

6. **添加初始数据源 / Add initial data sources**

```bash
docker exec newsradar-collector python scripts/add_sources.py
```

---

## 开发环境 / Development

### 前端开发 / Frontend Development

```bash
cd web

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local
# 编辑 .env.local，设置 NEXT_PUBLIC_API_URL=http://localhost:8001

# 启动开发服务器
npm run dev
# http://localhost:3000
```

### API 开发 / API Development

```bash
cd api

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env

# 数据库迁移
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload --port 8001
# API Docs: http://localhost:8001/docs
```

### 采集器开发 / Collector Development

```bash
cd clue-collector

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium

# 配置环境变量
cp .env.example .env

# 数据库迁移
alembic upgrade head

# 启动定时调度
python -m app.scheduler.scheduler
```

---

## API 端点 / API Endpoints

| 端点 / Endpoint | 方法 / Method | 说明 / Description |
|---|---|---|
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/me` | GET | 获取当前用户信息 |
| `/api/dashboard` | GET | 获取仪表盘数据 |
| `/api/discovery` | GET | AI 选题发现 |
| `/api/discovery/refresh` | POST | 刷新 AI 发现结果 |
| `/api/outlines` | GET/POST | 大纲列表/创建 |
| `/api/outlines/{id}` | GET/PUT/DELETE | 大纲详情/更新/删除 |
| `/api/outlines/generate` | POST | AI 生成大纲 |
| `/api/workbench/articles` | GET/POST | 文章列表/创建 |
| `/api/workbench/articles/{id}` | GET/PUT/DELETE | 文章详情/更新/删除 |
| `/api/workbench/articles/{id}/ai-suggest` | POST | AI 写作建议 |
| `/api/kol` | GET/POST | KOL 列表/创建 |
| `/api/kol/{id}` | GET/PATCH/DELETE | KOL 详情/更新/删除 |
| `/api/kol/{id}/posts` | GET | 获取 KOL  posts |
| `/api/data-sources` | GET/POST | 数据源列表/创建 |
| `/api/data-sources/groups` | GET/POST | 数据源分组管理 |

完整 API 文档见：`http://<api-host>/docs` (Swagger UI)

---

## 配置说明 / Configuration

### 环境变量 / Environment Variables

| 变量 / Variable | 默认值 / Default | 说明 / Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/clue_collector` | PostgreSQL 连接字符串 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接字符串 |
| `JWT_SECRET_KEY` | `change-me-in-production` | JWT 签名密钥 |
| `JWT_EXPIRE_HOURS` | `24` | Token 过期时间（小时） |
| `QWEN_API_KEY` | — | 通义千问 API Key |
| `QWEN_API_BASE` | `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions` | Qwen API 地址 |
| `QWEN_MODEL` | `qwen-plus` | 默认模型 |
| `APP_PORT` | `8001` | API 服务端口 |
| `APP_DEBUG` | `true` | 调试模式 |
| `TRANSLATION_ENABLED` | `true` | 启用翻译功能 |
| `TRANSLATION_THINKING_ENABLED` | `false` | 启用翻译思考模式 |

---

## 数据库迁移 / Database Migrations

### API 服务迁移 / API Migrations

```bash
cd api

# 创建新迁移
alembic revision --autogenerate -m "describe your change"

# 升级到最新版本
alembic upgrade head

# 回滚一次
alembic downgrade -1

# 查看历史
alembic history
```

### 采集器迁移 / Collector Migrations

```bash
cd clue-collector

alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

---

## 常用操作 / Common Operations

### 手动触发采集 / Manual Collection

```bash
# 强制采集所有数据源
docker exec newsradar-collector python scripts/force_collect.py

# 分析今日热榜
docker exec newsradar-collector python scripts/analyze_tophub.py
```

### 查看日志 / View Logs

```bash
# 查看所有服务日志
docker compose logs -f

# 查看指定服务
docker compose logs -f api
docker compose logs -f web
docker compose logs -f collector
```

### 重启服务 / Restart Services

```bash
# 重启单个服务
docker compose restart api

# 重建并重启
docker compose up -d --build web
```

---

## 默认账号 / Default Credentials

| 用户名 / Username | 密码 / Password | 角色 / Role |
|---|---|---|
| `admin` | `admin` | Administrator |

> 生产环境请务必修改默认密码。

---

## 贡献指南 / Contributing

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'feat: add some feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 创建 Pull Request

---

## 许可证 / License

MIT License

---

## 相关资源 / Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS v4](https://tailwindcss.com/docs/v4-beta)
- [Qwen API Documentation](https://help.aliyun.com/zh/dashscope/)
