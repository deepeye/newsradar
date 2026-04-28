# 线索采集服务 (Clue Collector)

媒体每日选题会系统的数据采集子系统，负责从多个数据源定时采集热点内容。

## 功能特性

- 🔥 **多源采集**：支持微博、知乎、抖音、B站等主流平台热榜
- 👤 **账号监控**：追踪社交账号和短视频博主动态
- 🕷️ **智能反爬**：IP轮换、UA轮换、Cookie池、频率自适应
- 📊 **数据追踪**：热榜排名变化历史、采集执行日志
- ⚡ **高效调度**：分组调度策略，支持不同采集频率
- 🐳 **容器化部署**：Docker Compose 一键启动

## 技术栈

- **语言**: Python 3.12+
- **爬虫框架**: Scrapling + Playwright
- **ORM**: SQLAlchemy 2.0 (异步)
- **数据库**: PostgreSQL 15
- **缓存/队列**: Redis 7
- **部署**: Docker Compose

## 快速开始

### 1. 环境准备

```bash
# 复制环境变量文件
cp .env.example .env

# 编辑配置
vim .env
```

### 2. 启动服务

```bash
cd docker
docker compose up -d
```

### 3. 查看日志

```bash
docker compose logs -f clue-collector
```

## 项目结构

```
clue-collector/
├── app/
│   ├── main.py                 # 服务入口
│   ├── config.py               # 配置管理
│   ├── scheduler/              # 调度模块
│   │   ├── scheduler.py        # 分组调度器
│   │   ├── task_runner.py      # 任务执行器
│   │   └── task_queue.py       # Redis任务队列
│   ├── collectors/             # 采集模块
│   │   ├── base.py             # 采集器基类
│   │   ├── configurable.py     # 配置化采集器
│   │   ├── adaptors/           # 框架适配器
│   │   └── plugins/            # 插件化采集器
│   ├── anti_crawl/             # 反爬防护模块
│   │   ├── ip_pool.py          # IP轮换池
│   │   ├── ua_rotator.py       # UA轮换
│   │   ├── cookie_pool.py      # Cookie池
│   │   ├── rate_limiter.py     # 频率控制
│   │   └── manager.py          # 统一入口
│   ├── error_handler/          # 异常处理模块
│   │   ├── error_classifier.py # 错误分类
│   │   ├── retry_handler.py    # 重试策略
│   │   ├── degradation.py      # 降级策略
│   │   └── alerts.py           # 告警机制
│   ├── storage/                # 存储模块
│   │   ├── models.py           # 数据模型
│   │   └── repository.py       # 数据访问层
│   └── utils/                  # 工具模块
│       └── logger.py           # 结构化日志
├── migrations/                 # 数据库迁移
├── tests/                      # 测试
├── docker/                     # Docker配置
│   ├── Dockerfile
│   └── docker-compose.yml
├── config/                     # 配置文件
│   ├── settings.yaml
│   └── proxy_providers.yaml
└── requirements.txt
```

## 配置说明

### 数据源配置

在数据库中配置 `data_sources` 表，指定采集规则：

```json
{
  "name": "微博热搜",
  "type": "hotlist",
  "collector_type": "configurable",
  "config": {
    "url": "https://weibo.com/hot",
    "method": "GET",
    "parse_type": "css",
    "parse_rules": {
      "container": ".hot-list li",
      "title": ".title",
      "rank": ".rank",
      "heat": ".heat-value"
    }
  }
}
```

### 代理配置

编辑 `config/proxy_providers.yaml` 配置代理池：

```yaml
providers:
  external_api:
    name: "external"
    type: "api"
    endpoint: "https://your-proxy-api.com/get"
    api_key: "your-api-key"
```

## 开发

### 本地开发环境

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行迁移
alembic upgrade head

# 启动服务
python -m app.main
```

### 运行测试

```bash
# 单元测试
pytest tests/unit -v

# 集成测试
pytest tests/integration -v

# 覆盖率报告
pytest --cov=app --cov-report=html
```

## License

MIT
