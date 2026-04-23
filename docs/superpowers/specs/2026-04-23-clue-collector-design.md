# 线索采集服务设计文档

## 概述

线索采集服务是媒体每日选题会系统的第一个子系统，负责从多个数据源（平台热榜、社交账号、短视频平台）定时采集数据，为后续的选题分析提供数据基础。

## 系统架构

采用单服务 + 内置调度架构，所有模块在单一 Python 服务中运行，通过函数调用协作。

### 核心组件

| 组件 | 职责 |
|------|------|
| Scheduler | 分组调度器，管理采集任务触发 |
| TaskRunner | 任务执行器，消费队列执行采集 |
| Collectors | 采集引擎（配置化 + 插件化） |
| AntiCrawlModule | 反爬防护统一入口 |
| ErrorHandler | 异常处理与告警 |
| Storage | PostgreSQL 数据存储 |

### 依赖服务

- **PostgreSQL**：数据源配置 + 采集数据持久化
- **Redis**：任务队列 + Cookie池 + 缓存
- **代理服务**：外部代理池 API

## 数据模型

### source_groups（数据源分组）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| name | VARCHAR(100) | 分组名称 |
| collect_interval | INTEGER | 采集频率（分钟） |
| is_active | BOOLEAN | 是否启用 |
| created_at, updated_at | TIMESTAMP | 时间戳 |

### data_sources（数据源配置）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| group_id | UUID FK | 所属分组 |
| name | VARCHAR(100) | 数据源名称 |
| type | ENUM | 类型：hotlist/account/video/custom |
| collector_type | ENUM | 采集器类型：configurable/plugin |
| config | JSONB | 采集配置（URL、解析规则等） |
| priority | INTEGER | 优先级（1-10） |
| is_active | BOOLEAN | 是否启用 |
| status | ENUM | 状态：active/paused/error |

### clues（采集线索数据）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| source_id | UUID FK | 数据源ID |
| title | VARCHAR(500) | 标题/内容摘要 |
| url | TEXT | 原始链接 |
| cover_image | TEXT | 图片/视频封面URL |
| author | VARCHAR(100) | 作者信息 |
| rank | INTEGER | 排名（热榜类） |
| heat_value | VARCHAR(100) | 热度值 |
| likes, comments, shares | INTEGER | 互动数据 |
| tags | JSONB | 话题标签数组 |
| collected_at | TIMESTAMP | 采集时间 |
| unique_hash | VARCHAR(64) | 去重哈希 |

### hotlist_history（热榜变化历史）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| clue_id | UUID FK | 关联线索 |
| change_type | ENUM | 变化类型：new/rank_up/rank_down/off |
| old_rank, new_rank | INTEGER | 排名变化 |
| recorded_at | TIMESTAMP | 记录时间 |

### collect_logs（采集执行日志）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| source_id | UUID FK | 数据源ID |
| status | ENUM | 状态：success/failed/partial |
| items_count | INTEGER | 采集条数 |
| error_type | VARCHAR(50) | 错误类型 |
| error_message | TEXT | 错误详情 |
| retry_count | INTEGER | 重试次数 |
| started_at, finished_at | TIMESTAMP | 开始/结束时间 |

## 采集器设计

### 配置化采集器

适用于热榜类数据源，通过 JSON 配置描述采集规则：

```json
{
  "url": "https://weibo.com/hot",
  "method": "GET",
  "parse_type": "css",
  "parse_rules": {
    "container": ".hot-list li",
    "title": ".title",
    "rank": ".rank",
    "heat": ".heat-value",
    "link": "a[href]"
  }
}
```

支持的解析类型：CSS选择器、JSON API、XPath

适用数据源：微博热搜、知乎热榜、抖音热点、今日头条、百度热搜、B站热门等

### 插件化采集器

适用于复杂数据源，继承 BaseCollector 接口：

```python
class BaseCollector(ABC):
    name: str
    version: str
    supported_types: list

    async def collect(self, source: DataSource, anti_crawl: AntiCrawlModule) -> List[ClueData]
    async def validate(self, config: dict) -> bool
```

插件需要处理：登录态保持、Cookie管理、动态渲染、反爬对抗

适用数据源：微信公众号、微博大V、抖音账号、小红书博主、自定义API源

### Scrapling 框架集成

- `FetchAdaptor`：配置化采集，自动适应页面变化
- `PlaywrightAdaptor`：插件化采集，隐身模式 + 动态渲染

## 反爬防护模块

### IP轮换池

- 支持外部代理池 API 接入
- IP健康检测（可用性、响应速度）
- 失败自动切换下一个IP
- Redis缓存可用IP列表

### UA轮换

- 预置主流浏览器UA池
- 按平台匹配UA（移动端/桌面端）
- 每次请求随机选取

### Cookie池

- Redis存储登录态Cookie
- Cookie有效性检测
- 过期自动刷新/更换
- 按数据源隔离Cookie

### 频率自适应

- 默认请求间隔配置
- 检测到限制（429/403）自动降频
- 正常后逐步恢复频率
- 随机延迟防检测

## 调度器设计

### 分组调度策略

| 分组 | 采集频率 | 采集策略 |
|------|----------|----------|
| 热榜组 | 5 分钟 | 增量采集（追踪变化） |
| 社交账号组 | 30 分钟 | 全量去重入库 |
| 短视频组 | 30 分钟 | 全量去重入库 |
| 自定义源组 | 可配置 | 按数据源类型决定 |

### Redis任务队列

- 支持优先级排序
- 失败重试队列
- 任务超时处理

### 调度流程

分组扫描 → 判断触发 → 创建任务 → 推入队列 → Worker消费 → 执行采集 → 存储结果 → 更新状态

### 核心类

```python
class Scheduler:
    async def run(self)          # 主循环，每分钟扫描
    def should_trigger(group)    # 判断是否触发采集
    def create_tasks(group)      # 创建采集任务

class TaskRunner:
    async def run(self)          # 消费队列
    async def execute_task(task) # 执行单个采集任务
```

## 异常处理模块

### 错误分类

| 错误类型 | 触发条件 | 处理策略 |
|----------|----------|----------|
| network_timeout | 请求超时 | 重试3次，每次更换IP |
| connection_error | 连接失败 | 重试2次，检查代理 |
| blocked_ip | 403/429状态码 | 立即切换IP，降频采集 |
| parse_error | 解析失败 | 记录日志，通知管理员 |
| cookie_expired | 登录态失效 | 切换下一个Cookie |
| source_unavailable | 源站不可访问 | 暂停数据源，等待恢复 |

### 重试策略

- 最大重试次数：3次
- 延迟策略：指数退避（5s → 10s → 20s）
- 可重试错误：network_timeout, connection_error, blocked_ip, cookie_expired
- 不重试错误：parse_error, source_unavailable

### 降级策略

1. **IP降级**：连续3次IP被封 → 标记不可用 → 切换新IP
2. **频率降级**：检测到429 → 降低50%频率 → 成功5次后恢复
3. **数据源降级**：连续5次失败 → 状态改为 error → 暂停采集

### 告警机制

触发条件：
- 数据源连续5次采集失败
- 数据源状态变更为 paused
- 解析规则失效（parse_error 连续3次）
- 代理池可用IP低于阈值
- Cookie池全部失效

告警方式：日志记录、邮件通知、Webhook（企业微信/钉钉）、Slack

## 项目结构

```
clue-collector/
├── app/
│   ├── main.py                 # 服务入口
│   ├── config.py               # 配置管理
│   ├── scheduler/              # 调度模块
│   ├── collectors/             # 采集模块
│   │   ├── configurable.py     # 配置化采集器
│   │   └── plugins/            # 插件化采集器
│   ├── anti_crawl/             # 反爬防护模块
│   ├── error_handler/          # 异常处理模块
│   ├── storage/                # 存储模块
│   └── utils/                  # 工具模块
├── migrations/                 # 数据库迁移
├── tests/                      # 测试
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── config/
│   ├── settings.yaml
│   └── proxy_providers.yaml
├── requirements.txt
└── README.md
```

## 部署配置

### Docker Compose 服务

| 服务 | 镜像 | 说明 |
|------|------|------|
| clue-collector | 自建 | 采集服务主进程 |
| postgres | postgres:15-alpine | 数据持久化 |
| redis | redis:7-alpine | 任务队列 + 缓存 |

### 启动命令

```bash
# 创建环境变量文件
cp .env.example .env

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f clue-collector
```

## 依赖库

| 库名 | 用途 |
|------|------|
| scrapling | 爬虫框架 |
| sqlalchemy | ORM |
| alembic | 数据库迁移 |
| asyncpg | PostgreSQL异步驱动 |
| redis | Redis客户端 |
| pyyaml | 配置解析 |
| pydantic | 配置验证 |
| structlog | 结构化日志 |
| httpx | HTTP客户端 |
| tenacity | 重试库 |

## 开发语言与技术栈

- **语言**：Python 3.11+
- **爬虫框架**：Scrapling
- **ORM**：SQLAlchemy 2.0
- **数据库**：PostgreSQL 15
- **缓存/队列**：Redis 7
- **部署**：Docker Compose

---

*设计文档版本：v1.0*
*创建日期：2026-04-23*