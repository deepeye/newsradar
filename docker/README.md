# Docker 部署指南

## 快速启动

```bash
# 1. 创建环境变量文件（从项目根目录运行）
cp docker/.env.example .env

# 2. 编辑 .env 文件，填入 QWEN_API_KEY
vim .env

# 3. 启动所有服务
docker compose -f docker/docker-compose.yml up -d

# 4. 查看服务状态
docker compose -f docker/docker-compose.yml ps
```

## 服务列表

| 服务 | 端口 | 说明 |
|------|------|------|
| nginx | 8084 | 统一入口 (外部反向代理转发至此) |
| web | 3000 | Next.js 前端 |
| api | 8001 | FastAPI 后端 |
| collector | - | 爬虫服务 |
| postgres | 5432 | PostgreSQL 数据库 |
| redis | 6379 | Redis 缓存 |

## 路由配置

内部 nginx 监听 `8084` 端口，路由规则：

| 路径 | 目标服务 |
|------|----------|
| `/newsradar/` | web:3000 (前端页面) |
| `/newsradar/api/` | api:8001 (后端 API) |
| `/newsradar/health` | 健康检查 |

**外部 nginx 配置示例：**
```nginx
location /newsradar {
    proxy_pass http://localhost:8084;
}
```

## 单独启动服务

```bash
# 仅启动基础设施
docker compose -f docker/docker-compose.yml up -d postgres redis

# 仅启动前端
docker compose -f docker/docker-compose.yml up -d web

# 仅启动 API
docker compose -f docker/docker-compose.yml up -d api

# 仅启动爬虫
docker compose -f docker/docker-compose.yml up -d collector
```

## 停止服务

```bash
docker compose -f docker/docker-compose.yml down

# 停止并删除数据卷
docker compose -f docker/docker-compose.yml down -v
```

## 查看日志

```bash
# 所有服务日志
docker compose -f docker/docker-compose.yml logs -f

# 单个服务日志
docker compose -f docker/docker-compose.yml logs -f api
docker compose -f docker/docker-compose.yml logs -f web
docker compose -f docker/docker-compose.yml logs -f collector
docker compose -f docker/docker-compose.yml logs -f nginx
```

## 重新构建

```bash
# 重新构建所有服务
docker compose -f docker/docker-compose.yml build --no-cache

# 重新构建单个服务
docker compose -f docker/docker-compose.yml build --no-cache api
```

## 访问地址

- **通过外部 nginx**: `http://your-domain/newsradar/`
- **直接访问 (开发调试)**:
  - 前端: `http://localhost:3000/`
  - API: `http://localhost:8001/api/`