# API 服务设计文档

## 概述

API 服务是媒体每日选题会系统的后端服务层，负责为前端提供 REST API、调用 AI 服务生成选题/大纲/建议、聚合爬虫采集的数据。

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Next.js)                        │
│  Dashboard │ AI Discovery │ Outlines │ Workbench │ Login    │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ REST API + JWT
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     API Server (FastAPI)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Auth       │  │  Dashboard  │  │  Discovery  │         │
│  │  Service    │  │  Service    │  │  Service    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Outlines   │  │  Workbench  │  │  AI         │         │
│  │  Service    │  │  Service    │  │  Service    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                              │                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    Repository Layer                   │  │
│  │  ClueRepo │ DataSourceRepo │ OutlineRepo │ ArticleRepo│  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                              │              │
         │ SQL                          │ SQL          │ HTTP
         ▼                              ▼              ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  PostgreSQL     │  │  PostgreSQL     │  │  阿里云百炼      │
│  (clue-collector│  │  (api-server    │  │  (Qwen API)     │
│   tables)       │  │   tables)       │  │                 │
│                 │  │                 │  │  qwen3.6-35b-a3b│
│  clues          │  │  users          │  │                 │
│  data_sources   │  │  org_configs    │  │                 │
│  hotlist_history│  │  outlines       │  │                 │
│  collect_logs   │  │  articles       │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

**关键设计点**：

1. **共享 PostgreSQL**：API 服务连接同一个数据库，读取 clue-collector 的表，新增自己的业务表
2. **分层架构**：Router → Service → Repository，职责清晰
3. **AI Service 集中管理**：所有 LLM 调用集中在 `ai_service.py`，便于管理 prompt 模板和 API 成本
4. **JWT 认证**：账号密码登录，后续请求携带 Bearer Token

## 技术栈

| 层级 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| ORM | SQLAlchemy 2.0（异步） |
| 数据库 | PostgreSQL 15（共享 clue-collector） |
| 缓存 | Redis 7 |
| 认证 | JWT（python-jose） |
| AI 服务 | 阿里云百炼（qwen3.6-35b-a3b） |
| HTTP 客户端 | httpx |
| 日志 | structlog |
| 重试 | tenacity |

## 数据库设计

API 服务新增以下表，与 clue-collector 共享 PostgreSQL：

### users（用户表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| username | VARCHAR(50) | 用户名，唯一 |
| password_hash | VARCHAR(255) | bcrypt 哈希密码 |
| display_name | VARCHAR(100) | 显示名称 |
| role | ENUM | 角色：admin/editor/viewer |
| is_active | BOOLEAN | 是否启用 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### org_configs（组织配置表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| name | VARCHAR(100) | 组织名称 |
| domains | JSONB | 关注领域数组 |
| style | JSONB | 报道风格数组 |
| is_active | BOOLEAN | 是否启用 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

单条记录，全局配置。

### topic_outlines（选题大纲表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| title | VARCHAR(500) | 选题标题 |
| summary | TEXT | 概要描述 |
| urgency | VARCHAR(20) | 紧急程度：高/中/低 |
| info_density | INTEGER | 信息密度评分（0-100） |
| headlines | JSONB | AI 生成的标题建议数组 |
| lead_paragraph | TEXT | 导语段落 |
| outline_sections | JSONB | 大纲结构（JSON 数组） |
| interview_directions | JSONB | 采访方向数组 |
| references | JSONB | 参考资料链接数组 |
| source_clue_ids | JSONB | 关联的线索 ID |
| ai_model | VARCHAR(50) | 生成使用的 AI 模型 |
| created_by | UUID FK | 创建用户 |
| status | ENUM | 状态：draft/approved/archived |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### articles（文章草稿表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| outline_id | UUID FK | 关联选题大纲（可选） |
| title | VARCHAR(500) | 文章标题 |
| author_id | UUID FK | 作者用户 |
| content | TEXT | 正文内容（Markdown） |
| word_count | INTEGER | 字数统计 |
| target_word_count | INTEGER | 目标字数 |
| urgent | BOOLEAN | 是否紧急 |
| ai_suggestions | JSONB | AI 写作建议数组 |
| metrics | JSONB | AI 评分 |
| references | JSONB | 参考文档数组 |
| status | ENUM | 状态：draft/reviewing/published |
| last_saved_at | TIMESTAMP | 最后保存时间 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## API 端点设计

### 认证 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录，返回 JWT token |
| GET | `/api/auth/me` | 获取当前用户信息 |

**注**：JWT 无状态认证，登出由前端清除 token 实现，后端不提供 logout 端点。

### Dashboard API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/dashboard` | 获取聚合数据 |

### Discovery API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/discovery` | 获取 AI 选题推荐列表 |
| GET | `/api/discovery/config` | 获取组织配置 |
| PUT | `/api/discovery/config` | 更新组织配置 |
| POST | `/api/discovery/refresh` | 刷新 AI 推荐 |

### Outlines API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/outlines` | 获取选题大纲列表 |
| GET | `/api/outlines/{id}` | 获取单个大纲详情 |
| POST | `/api/outlines` | 创建选题大纲 |
| PUT | `/api/outlines/{id}` | 更新选题大纲 |
| DELETE | `/api/outlines/{id}` | 删除选题大纲 |
| POST | `/api/outlines/generate` | 从线索生成大纲（AI） |
| POST | `/api/outlines/{id}/regenerate` | 重新生成某部分 |

### Workbench API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/workbench/articles` | 获取文章列表 |
| GET | `/api/workbench/articles/{id}` | 获取文章详情 |
| POST | `/api/workbench/articles` | 创建文章草稿 |
| PUT | `/api/workbench/articles/{id}` | 保存文章 |
| DELETE | `/api/workbench/articles/{id}` | 删除文章 |
| POST | `/api/workbench/articles/{id}/ai-suggest` | 获取 AI 写作建议 |
| POST | `/api/workbench/articles/{id}/ai-metrics` | 获取 AI 评分 |

**总计：21 个 API 端点**

## AI Service 设计

### 供应商配置

| 配置项 | 值 |
|--------|-----|
| 供应商 | 阿里云百炼 |
| 默认模型 | qwen3.6-35b-a3b |
| API 接入 | HTTP REST API |
| 超时时间 | 300 秒 |

### AI 功能清单

| 功能 | 输入 | 输出 |
|------|------|------|
| 选题推荐 | 组织配置 + 线索数据 | 推荐选题列表 |
| 大纲生成 | 线索 + 组织配置 | 完整大纲 |
| 标题生成 | 已有大纲 | 3 个风格标题 |
| 写作建议 | 标题 + 正文 | 改进建议列表 |
| 内容评分 | 正文内容 | 客观性、可读性评分 |

### 成本控制

| 策略 | 实现 |
|------|------|
| 模型选择 | 默认 qwen3.6-35b-a3b |
| 输入截断 | 只取热度最高线索 |
| 结果缓存 | Redis 缓存 5 分钟 |
| 异步调用 | 后台生成，不阻塞 |
| 错误降级 | 返回预设模板或缓存 |

## 项目结构

```
api-server/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/                    # 路由层
│   │   ├── deps.py
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── discovery.py
│   │   ├── outlines.py
│   │   └── workbench.py
│   ├── services/               # 业务逻辑层
│   │   ├── auth_service.py
│   │   ├── dashboard_service.py
│   │   ├── discovery_service.py
│   │   ├── outlines_service.py
│   │   ├── workbench_service.py
│   │   └── ai_service.py
│   ├── repositories/           # 数据访问层
│   │   ├── base.py
│   │   ├── user_repo.py
│   │   ├── org_config_repo.py
│   │   ├── clue_repo.py
│   │   ├── data_source_repo.py
│   │   ├── outline_repo.py
│   │   └── article_repo.py
│   ├── models/                 # SQLAlchemy 模型
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── org_config.py
│   │   ├── outline.py
│   │   ├── article.py
│   │   └── clue.py
│   ├── schemas/                # Pydantic 模型
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── discovery.py
│   │   ├── outlines.py
│   │   ├── workbench.py
│   │   └── common.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── database.py
│   │   └── exceptions.py
│   └── utils/
│       ├── logger.py
│       └── cache.py
├── migrations/
├── tests/
├── docker/
├── scripts/
├── requirements.txt
├── .env.example
└── README.md
```

## 迁移策略

独立 Alembic，但共享同一个 PostgreSQL 数据库：
- api-server 迁移只操作自己的表（users、org_configs、topic_outlines、articles）
- 读取 clue-collector 的表时只做模型映射，不执行迁移

**clue-collector 表引用**（详见 `docs/superpowers/specs/2026-04-23-clue-collector-design.md`）：
- `source_groups`：数据源分组
- `data_sources`：数据源配置
- `clues`：采集线索数据
- `hotlist_history`：热榜变化历史
- `collect_logs`：采集执行日志
- `cookie_pool`：Cookie池条目

## 环境变量

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/clue_collector

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# 阿里云百炼
QWEN_API_KEY=your-api-key
QWEN_MODEL=qwen3.6-35b-a3b
QWEN_TIMEOUT=300

# 应用
APP_ENV=development
APP_DEBUG=true
APP_PORT=8001
```

## 部署

### Docker Compose（合并 clue-collector）

```yaml
services:
  clue-collector:
    build: ./clue-collector/docker
    depends_on: [postgres, redis]

  api-server:
    build: ./api-server/docker
    ports: ["8001:8001"]
    depends_on: [postgres, redis]

  postgres:
    image: postgres:15-alpine
    ...

  redis:
    image: redis:7-alpine
    ...
```

### 生产启动

```bash
gunicorn -k uvicorn.workers.UvicornWorker \
  app.main:app \
  --bind 0.0.0.0:8001 \
  --workers 4 \
  --timeout 300
```

## 依赖清单

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
httpx>=0.27.0
redis>=5.0.0
tenacity>=8.2.0
structlog>=24.1.0
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
```

---

*设计文档版本：v1.0*
*创建日期：2026-04-28*