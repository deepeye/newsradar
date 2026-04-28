# API Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the API server service for the media daily topic system, providing REST APIs for the Next.js frontend and integrating with Alibaba Cloud Bailian for AI features.

**Architecture:** Layered FastAPI service (Router → Service → Repository) sharing PostgreSQL with clue-collector. JWT authentication for all endpoints except login. AI features powered by Qwen API with centralized prompt management and Redis caching.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL 15, Redis 7, python-jose (JWT), httpx (AI API), structlog, tenacity

---

## File Structure

```
api-server/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI app, CORS, lifespan
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                      # get_db, get_current_user
│   │   ├── auth.py                      # POST /api/auth/login, GET /api/auth/me
│   │   ├── dashboard.py                 # GET /api/dashboard
│   │   ├── discovery.py                 # GET/PUT /api/discovery/config, GET /api/discovery, POST /api/discovery/refresh
│   │   ├── outlines.py                  # CRUD + generate + regenerate
│   │   └── workbench.py                 # CRUD + ai-suggest + ai-metrics
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py              # JWT create/verify, password hash
│   │   ├── dashboard_service.py         # Aggregate clues + data_sources + AI
│   │   ├── discovery_service.py         # Org config + AI recommendations
│   │   ├── outlines_service.py          # Outline CRUD + AI generate
│   │   ├── workbench_service.py         # Article CRUD + AI suggest/metrics
│   │   └── ai_service.py               # Qwen API calls + prompt templates
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py                      # BaseRepository with generic CRUD
│   │   ├── user_repo.py
│   │   ├── org_config_repo.py
│   │   ├── clue_repo.py                 # Read-only access to clues table
│   │   ├── data_source_repo.py          # Read-only access to data_sources table
│   │   ├── outline_repo.py
│   │   └── article_repo.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                      # DeclarativeBase + shared columns
│   │   ├── user.py                      # User model
│   │   ├── org_config.py                # OrgConfig model
│   │   ├── outline.py                   # TopicOutline model
│   │   ├── article.py                   # Article model
│   │   └── clue.py                      # Clue model (read-only mapping)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── discovery.py
│   │   ├── outlines.py
│   │   ├── workbench.py
│   │   └── common.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                    # Settings
│   │   ├── security.py                  # JWT + password hashing
│   │   ├── database.py                  # Async engine + session factory
│   │   └── exceptions.py               # Custom exceptions
│   └── utils/
│       ├── __init__.py
│       ├── logger.py                    # Structured logging (from clue-collector pattern)
│       └── cache.py                     # Redis cache wrapper
├── migrations/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_dashboard.py
│   │   ├── test_discovery.py
│   │   ├── test_outlines.py
│   │   └── test_workbench.py
│   └── test_services/
│       ├── __init__.py
│       └── test_ai_service.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── scripts/
│   ├── init_db.py
│   └── seed_data.py
├── alembic.ini
├── requirements.txt
├── .env.example
└── README.md
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `api-server/app/__init__.py`
- Create: `api-server/app/core/__init__.py`
- Create: `api-server/app/core/config.py`
- Create: `api-server/app/core/database.py`
- Create: `api-server/app/core/security.py`
- Create: `api-server/app/core/exceptions.py`
- Create: `api-server/app/utils/__init__.py`
- Create: `api-server/app/utils/logger.py`
- Create: `api-server/app/utils/cache.py`
- Create: `api-server/app/main.py`
- Create: `api-server/requirements.txt`
- Create: `api-server/.env.example`
- Create: `api-server/app/api/__init__.py`
- Create: `api-server/app/api/deps.py`
- Create: `api-server/app/services/__init__.py`
- Create: `api-server/app/repositories/__init__.py`
- Create: `api-server/app/schemas/__init__.py`
- Create: `api-server/app/models/__init__.py`

- [ ] **Step 1: Create directory structure**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent
mkdir -p api-server/app/{api,services,repositories,models,schemas,core,utils}
mkdir -p api-server/{migrations/versions,tests/test_api,tests/test_services,docker,scripts}
touch api-server/app/__init__.py
touch api-server/app/api/__init__.py
touch api-server/app/services/__init__.py
touch api-server/app/repositories/__init__.py
touch api-server/app/schemas/__init__.py
touch api-server/app/models/__init__.py
touch api-server/app/core/__init__.py
touch api-server/app/utils/__init__.py
touch api-server/tests/__init__.py
touch api-server/tests/test_api/__init__.py
touch api-server/tests/test_services/__init__.py
```

- [ ] **Step 2: Create requirements.txt**

```txt
# Web framework
fastapi>=0.110.0
uvicorn[standard]>=0.27.0

# ORM
sqlalchemy>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0

# Validation
pydantic>=2.0.0
pydantic-settings>=2.0.0

# Auth
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# HTTP client (AI API)
httpx>=0.27.0

# Redis
redis>=5.0.0

# Utilities
tenacity>=8.2.0
structlog>=24.1.0
python-dotenv>=1.0.0

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
```

- [ ] **Step 3: Create .env.example**

```bash
# Database (shared with clue-collector)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/clue_collector

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# Alibaba Cloud Bailian (Qwen)
QWEN_API_KEY=your-qwen-api-key
QWEN_MODEL=qwen3.6-35b-a3b
QWEN_TIMEOUT=300

# App
APP_ENV=development
APP_DEBUG=true
APP_PORT=8001
```

- [ ] **Step 4: Create core/config.py**

```python
"""Application configuration"""
import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global settings"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    # App
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_PORT: int = 8001

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/clue_collector"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    # Qwen AI
    QWEN_API_KEY: str = ""
    QWEN_MODEL: str = "qwen3.6-35b-a3b"
    QWEN_TIMEOUT: int = 300
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

    # AI Cache
    AI_CACHE_TTL: int = 300  # 5 minutes


settings = Settings()
```

- [ ] **Step 5: Create core/database.py**

```python
"""Database connection management"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)

from app.core.config import settings


class DatabaseManager:
    """Database manager"""

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker[AsyncSession] | None = None

    async def initialize(self) -> None:
        self._engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
        )
        self._session_maker = async_sessionmaker(
            self._engine,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    async def close(self) -> None:
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_maker = None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        if not self._session_maker:
            raise RuntimeError("Database not initialized")
        async with self._session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions"""
    async with db_manager.session() as session:
        yield session
```

- [ ] **Step 6: Create core/security.py**

```python
"""JWT and password hashing"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=settings.JWT_EXPIRE_HOURS)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None
```

- [ ] **Step 7: Create core/exceptions.py**

```python
"""Custom exceptions"""


class AppException(Exception):
    """Base application exception"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403)


class BadRequestException(AppException):
    def __init__(self, message: str = "Bad request"):
        super().__init__(message, status_code=400)


class AIServiceError(Exception):
    """AI service exception"""
    pass


class AIServiceTimeoutError(AIServiceError):
    pass


class AIServiceRateLimitError(AIServiceError):
    pass


class AIServiceContentError(AIServiceError):
    pass
```

- [ ] **Step 8: Create utils/logger.py**

```python
"""Structured logging configuration"""
import sys
import logging

import structlog


def configure_logging(log_level: str = "INFO") -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
```

- [ ] **Step 9: Create utils/cache.py**

```python
"""Redis cache wrapper"""
import json
from typing import Optional, Any

import redis.asyncio as aioredis

from app.core.config import settings


class CacheManager:
    """Async Redis cache manager"""

    def __init__(self) -> None:
        self._client: Optional[aioredis.Redis] = None

    async def initialize(self) -> None:
        self._client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    async def get(self, key: str) -> Optional[Any]:
        if not self._client:
            return None
        value = await self._client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        if not self._client:
            return
        serialized = json.dumps(value, ensure_ascii=False, default=str)
        await self._client.set(key, serialized, ex=ttl)

    async def delete(self, key: str) -> None:
        if not self._client:
            return
        await self._client.delete(key)


cache_manager = CacheManager()
```

- [ ] **Step 10: Create api/deps.py**

```python
"""FastAPI dependencies"""
from typing import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException
from app.repositories.user_repo import UserRepository

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Extract and validate current user from JWT token"""
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    repo = UserRepository(db)
    user = await repo.get_by_id(UUID(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return {
        "id": str(user.id),
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role,
    }
```

- [ ] **Step 11: Create main.py**

```python
"""FastAPI application entry point"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import db_manager
from app.utils.cache import cache_manager
from app.utils.logger import configure_logging, get_logger
from app.core.exceptions import AppException


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging("DEBUG" if settings.APP_DEBUG else "INFO")
    logger = get_logger("api-server")
    logger.info("application_starting")

    await db_manager.initialize()
    logger.info("database_initialized")

    await cache_manager.initialize()
    logger.info("cache_initialized")

    yield

    logger.info("application_shutting_down")
    await cache_manager.close()
    logger.info("cache_closed")
    await db_manager.close()
    logger.info("database_closed")


app = FastAPI(
    title="NewsRadar API Server",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


# Routers will be included in later tasks
# from app.api import auth, dashboard, discovery, outlines, workbench
```

- [ ] **Step 12: Create venv and install dependencies**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 13: Verify imports work**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -c "from app.core.config import settings; print(settings.APP_PORT)"
```

Expected: `8001`

- [ ] **Step 14: Commit**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent
git add api-server/
git commit -m "feat: scaffold api-server project structure with core modules"
```

---

### Task 2: SQLAlchemy Models and Alembic Migration

**Files:**
- Create: `api-server/app/models/base.py`
- Create: `api-server/app/models/user.py`
- Create: `api-server/app/models/org_config.py`
- Create: `api-server/app/models/outline.py`
- Create: `api-server/app/models/article.py`
- Create: `api-server/app/models/clue.py`
- Modify: `api-server/app/models/__init__.py`
- Create: `api-server/alembic.ini`
- Create: `api-server/migrations/env.py`
- Create: `api-server/migrations/script.py.mako`

- [ ] **Step 1: Write test for User model**

Create `api-server/tests/test_models/test_user_model.py`:

```python
"""Test User model creation"""
import pytest
from app.models.user import User, UserRole


def test_user_model_has_required_fields():
    """Verify User model fields are defined"""
    assert hasattr(User, "id")
    assert hasattr(User, "username")
    assert hasattr(User, "password_hash")
    assert hasattr(User, "display_name")
    assert hasattr(User, "role")
    assert hasattr(User, "is_active")


def test_user_role_enum():
    assert UserRole.ADMIN == "admin"
    assert UserRole.EDITOR == "editor"
    assert UserRole.VIEWER == "viewer"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -m pytest tests/test_models/test_user_model.py -v
```

Expected: FAIL — module not found

- [ ] **Step 3: Create models/base.py**

```python
"""Base model with shared columns"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class BaseModel(Base):
    """Abstract base with id, created_at, updated_at"""
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=func.now(), onupdate=func.now()
    )
```

- [ ] **Step 4: Create models/user.py**

```python
"""User model"""
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class UserRole(str, PyEnum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    display_name: Mapped[str] = mapped_column(
        String(100), nullable=False, default=""
    )
    role: Mapped[UserRole] = mapped_column(
        String(20), nullable=False, default=UserRole.VIEWER
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
```

- [ ] **Step 5: Create models/org_config.py**

```python
"""Organization configuration model"""
from sqlalchemy import String, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class OrgConfig(BaseModel):
    __tablename__ = "org_configs"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    domains: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list,
        comment="Focus areas e.g. ['财经', '民生']"
    )
    style: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list,
        comment="Reporting style e.g. ['客观', '严谨']"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
```

- [ ] **Step 6: Create models/outline.py**

```python
"""Topic outline model"""
from enum import Enum as PyEnum
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class OutlineStatus(str, PyEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    ARCHIVED = "archived"


class TopicOutline(BaseModel):
    __tablename__ = "topic_outlines"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    urgency: Mapped[str] = mapped_column(String(20), nullable=False, default="中")
    info_density: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    headlines: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    lead_paragraph: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outline_sections: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    interview_directions: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    references: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    source_clue_ids: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    ai_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_by: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    status: Mapped[OutlineStatus] = mapped_column(
        String(20), nullable=False, default=OutlineStatus.DRAFT
    )
```

- [ ] **Step 7: Create models/article.py**

```python
"""Article draft model"""
from enum import Enum as PyEnum
from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import String, Integer, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ArticleStatus(str, PyEnum):
    DRAFT = "draft"
    REVIEWING = "reviewing"
    PUBLISHED = "published"


class Article(BaseModel):
    __tablename__ = "articles"

    outline_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("topic_outlines.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="")
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    target_word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    urgent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ai_suggestions: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    metrics: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    references: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    status: Mapped[ArticleStatus] = mapped_column(
        String(20), nullable=False, default=ArticleStatus.DRAFT
    )
    last_saved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
```

- [ ] **Step 8: Create models/clue.py (read-only mapping)**

```python
"""Clue model — read-only mapping to clue-collector table"""
from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Clue(Base):
    """Read-only mapping — do NOT create migrations for this table"""
    __tablename__ = "clues"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )
    source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_image: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    heat_value: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    likes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    comments: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    shares: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    tags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    unique_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class DataSource(Base):
    """Read-only mapping — do NOT create migrations for this table"""
    __tablename__ = "data_sources"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )
    group_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("source_groups.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    collector_type: Mapped[str] = mapped_column(String(20), nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    is_active: Mapped[bool] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class SourceGroup(Base):
    """Read-only mapping — do NOT create migrations for this table"""
    __tablename__ = "source_groups"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    collect_interval: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    is_active: Mapped[bool] = mapped_column(Integer, nullable=False, default=1)
```

- [ ] **Step 9: Update models/__init__.py**

```python
"""Models package"""
from app.models.base import Base, BaseModel
from app.models.user import User, UserRole
from app.models.org_config import OrgConfig
from app.models.outline import TopicOutline, OutlineStatus
from app.models.article import Article, ArticleStatus
from app.models.clue import Clue, DataSource, SourceGroup

__all__ = [
    "Base",
    "BaseModel",
    "User",
    "UserRole",
    "OrgConfig",
    "TopicOutline",
    "OutlineStatus",
    "Article",
    "ArticleStatus",
    "Clue",
    "DataSource",
    "SourceGroup",
]
```

- [ ] **Step 10: Create alembic.ini**

```ini
[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 11: Create migrations/env.py**

```python
"""Alembic migration environment"""
import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config, create_async_engine

from alembic import context

# Only import api-server models (NOT clue read-only models as Base)
from app.models.base import Base, BaseModel
from app.models.user import User
from app.models.org_config import OrgConfig
from app.models.outline import TopicOutline
from app.models.article import Article

config = context.config

database_url = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/clue_collector"
)
config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Only target api-server owned tables for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = create_async_engine(database_url, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 12: Create migrations/script.py.mako**

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 13: Initialize Alembic and generate first migration**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
alembic revision --autogenerate -m "create api_server tables"
```

Expected: Generates migration file in `migrations/versions/`

- [ ] **Step 14: Run migration against local database (requires running postgres)**

```bash
alembic upgrade head
```

Expected: Creates `users`, `org_configs`, `topic_outlines`, `articles` tables

- [ ] **Step 15: Run model tests**

```bash
python -m pytest tests/ -v
```

Expected: PASS

- [ ] **Step 16: Commit**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent
git add api-server/
git commit -m "feat: add SQLAlchemy models and Alembic migration setup"
```

---

### Task 3: Pydantic Schemas

**Files:**
- Create: `api-server/app/schemas/common.py`
- Create: `api-server/app/schemas/auth.py`
- Create: `api-server/app/schemas/dashboard.py`
- Create: `api-server/app/schemas/discovery.py`
- Create: `api-server/app/schemas/outlines.py`
- Create: `api-server/app/schemas/workbench.py`

- [ ] **Step 1: Write test for auth schemas**

Create `api-server/tests/test_schemas/test_auth_schemas.py`:

```python
"""Test auth schemas"""
import pytest
from pydantic import ValidationError
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo


def test_login_request_valid():
    req = LoginRequest(username="admin", password="secret")
    assert req.username == "admin"
    assert req.password == "secret"


def test_login_request_missing_fields():
    with pytest.raises(ValidationError):
        LoginRequest()


def test_user_info_schema():
    info = UserInfo(
        id="uuid-123",
        username="admin",
        display_name="管理员",
        role="admin",
    )
    assert info.role == "admin"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -m pytest tests/test_schemas/test_auth_schemas.py -v
```

Expected: FAIL

- [ ] **Step 3: Create schemas/common.py**

```python
"""Common schema fields"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
```

- [ ] **Step 4: Create schemas/auth.py**

```python
"""Auth request/response schemas"""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)


class UserInfo(BaseModel):
    id: str
    username: str
    display_name: str
    role: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo
```

- [ ] **Step 5: Create schemas/dashboard.py**

```python
"""Dashboard response schemas"""
from typing import Optional, List
from pydantic import BaseModel


class TrendingItem(BaseModel):
    id: str
    rank: int
    title: str
    heat_value: str
    status: Optional[str] = None
    url: Optional[str] = None


class PlatformTrendingCard(BaseModel):
    platform: str
    platform_label: str
    items: List[TrendingItem]
    last_updated: str


class KOLPost(BaseModel):
    id: str
    author: str
    verified: Optional[bool] = None
    content: str
    likes: int = 0
    shares: int = 0
    comments: int = 0
    time_ago: str = ""


class KOLColumn(BaseModel):
    platform: str
    platform_label: str
    posts: List[KOLPost]


class AISuggestion(BaseModel):
    id: str
    title: str
    description: str


class DashboardData(BaseModel):
    trending_cards: List[PlatformTrendingCard]
    kol_columns: List[KOLColumn]
    ai_suggestions: List[AISuggestion]
    active_threads: int = 0
    topic_alerts: int = 0
    quote: Optional[dict] = None
```

- [ ] **Step 6: Create schemas/discovery.py**

```python
"""AI Discovery request/response schemas"""
from typing import List, Optional
from pydantic import BaseModel, Field


class OrgConfigResponse(BaseModel):
    id: str
    name: str
    domains: List[str]
    style: List[str]


class OrgConfigUpdate(BaseModel):
    name: Optional[str] = None
    domains: Optional[List[str]] = None
    style: Optional[List[str]] = None


class AITopicRecommendation(BaseModel):
    id: str
    source: str
    source_icon: str
    tag: str
    title: str
    reason: str
    angles: List[str]


class DiscoveryResponse(BaseModel):
    org_config: OrgConfigResponse
    total_clues: int
    last_updated: str
    recommendations: List[AITopicRecommendation]
    total_recommendations: int
```

- [ ] **Step 7: Create schemas/outlines.py**

```python
"""Outlines request/response schemas"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class HeadlineSuggestion(BaseModel):
    style: str
    text: str


class OutlineItem(BaseModel):
    id: str
    content: str
    has_ai_rewrite: bool = False


class OutlineSection(BaseModel):
    id: str
    number: str
    title: str
    items: List[OutlineItem]


class InterviewDirection(BaseModel):
    id: str
    role: str
    description: str


class ReferenceLink(BaseModel):
    id: str
    title: str
    source: str
    url: Optional[str] = None


class OutlineGenerateRequest(BaseModel):
    clue_ids: List[str] = Field(..., min_length=1)
    additional_context: Optional[str] = None


class OutlineRegenerateRequest(BaseModel):
    section: str = Field(..., pattern="^(headlines|outline|interview)$")


class OutlineResponse(BaseModel):
    id: str
    title: str
    summary: Optional[str] = None
    urgency: str
    info_density: int
    headlines: Optional[List[HeadlineSuggestion]] = None
    lead_paragraph: Optional[str] = None
    outline_sections: Optional[List[OutlineSection]] = None
    interview_directions: Optional[List[InterviewDirection]] = None
    references: Optional[List[ReferenceLink]] = None
    source_clue_ids: Optional[List[str]] = None
    ai_model: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class OutlineListResponse(BaseModel):
    total: int
    items: List[OutlineResponse]


class OutlineCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    summary: Optional[str] = None
    urgency: str = "中"


class OutlineUpdateRequest(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    urgency: Optional[str] = None
    info_density: Optional[int] = None
    headlines: Optional[List[HeadlineSuggestion]] = None
    lead_paragraph: Optional[str] = None
    outline_sections: Optional[List[OutlineSection]] = None
    interview_directions: Optional[List[InterviewDirection]] = None
    references: Optional[List[ReferenceLink]] = None
    status: Optional[str] = None
```

- [ ] **Step 8: Create schemas/workbench.py**

```python
"""Workbench request/response schemas"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AISuggestionItem(BaseModel):
    id: str
    type: str
    original: str
    suggested: str
    reason: str


class ContentMetrics(BaseModel):
    objectivity: int = 0
    readability: str = ""


class ReferenceDoc(BaseModel):
    id: str
    title: str
    source: str
    last_updated: Optional[str] = None


class ArticleCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    outline_id: Optional[str] = None
    target_word_count: int = 1600
    urgent: bool = False


class ArticleUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    target_word_count: Optional[int] = None
    urgent: Optional[bool] = None
    status: Optional[str] = None


class ArticleResponse(BaseModel):
    id: str
    outline_id: Optional[str] = None
    title: str
    author_id: Optional[str] = None
    content: Optional[str] = None
    word_count: int
    target_word_count: int
    completion_percent: int
    urgent: bool
    ai_suggestions: Optional[List[AISuggestionItem]] = None
    metrics: Optional[ContentMetrics] = None
    references: Optional[List[ReferenceDoc]] = None
    status: str
    last_saved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ArticleListResponse(BaseModel):
    total: int
    items: List[ArticleResponse]
```

- [ ] **Step 9: Run all schema tests**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -m pytest tests/test_schemas/ -v
```

Expected: PASS

- [ ] **Step 10: Commit**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent
git add api-server/
git commit -m "feat: add Pydantic schemas for all API endpoints"
```

---

### Task 4: Repository Layer

**Files:**
- Create: `api-server/app/repositories/base.py`
- Create: `api-server/app/repositories/user_repo.py`
- Create: `api-server/app/repositories/org_config_repo.py`
- Create: `api-server/app/repositories/clue_repo.py`
- Create: `api-server/app/repositories/data_source_repo.py`
- Create: `api-server/app/repositories/outline_repo.py`
- Create: `api-server/app/repositories/article_repo.py`
- Modify: `api-server/app/repositories/__init__.py`

- [ ] **Step 1: Write test for UserRepository**

Create `api-server/tests/test_repositories/test_user_repo.py`:

```python
"""Test UserRepository"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.repositories.user_repo import UserRepository
from app.models.user import User, UserRole


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def user_repo(mock_session):
    return UserRepository(mock_session)


def test_user_repo_init(mock_session):
    repo = UserRepository(mock_session)
    assert repo.session == mock_session
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -m pytest tests/test_repositories/test_user_repo.py -v
```

Expected: FAIL

- [ ] **Step 3: Create repositories/base.py**

```python
"""Base repository with generic CRUD"""
from typing import Optional, TypeVar, Type, Sequence
from uuid import UUID

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository:
    """Base repository with common operations"""

    def __init__(self, session: AsyncSession, model_class: Type[ModelType]):
        self.session = session
        self.model_class = model_class

    async def get_by_id(self, item_id: UUID) -> Optional[ModelType]:
        result = await self.session.execute(
            select(self.model_class).where(self.model_class.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ModelType]:
        result = await self.session.execute(
            select(self.model_class)
            .order_by(self.model_class.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def count(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(self.model_class)
        )
        return result.scalar_one()

    async def delete_by_id(self, item_id: UUID) -> bool:
        result = await self.session.execute(
            delete(self.model_class).where(self.model_class.id == item_id)
        )
        return result.rowcount > 0
```

- [ ] **Step 4: Create repositories/user_repo.py**

```python
"""User repository"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        username: str,
        password_hash: str,
        display_name: str = "",
        role: UserRole = UserRole.VIEWER,
    ) -> User:
        user = User(
            username=username,
            password_hash=password_hash,
            display_name=display_name,
            role=role,
            is_active=True,
        )
        self.session.add(user)
        await self.session.flush()
        return user
```

- [ ] **Step 5: Create repositories/org_config_repo.py**

```python
"""Organization configuration repository"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.org_config import OrgConfig
from app.repositories.base import BaseRepository


class OrgConfigRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, OrgConfig)

    async def get_active(self) -> Optional[OrgConfig]:
        result = await self.session.execute(
            select(OrgConfig).where(OrgConfig.is_active == True).limit(1)
        )
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        name: str,
        domains: list,
        style: list,
    ) -> OrgConfig:
        existing = await self.get_active()
        if existing:
            existing.name = name
            existing.domains = domains
            existing.style = style
            await self.session.flush()
            return existing
        config = OrgConfig(
            name=name,
            domains=domains,
            style=style,
            is_active=True,
        )
        self.session.add(config)
        await self.session.flush()
        return config
```

- [ ] **Step 6: Create repositories/clue_repo.py**

```python
"""Clue repository — read-only access to clue-collector tables"""
from typing import Sequence, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clue import Clue, DataSource, SourceGroup
from app.repositories.base import BaseRepository


class ClueRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Clue)

    async def get_latest_by_source(
        self,
        source_id: UUID,
        limit: int = 20,
    ) -> Sequence[Clue]:
        result = await self.session.execute(
            select(Clue)
            .where(Clue.source_id == source_id)
            .order_by(Clue.collected_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_hot_by_source(
        self,
        source_id: UUID,
        limit: int = 10,
    ) -> Sequence[Clue]:
        result = await self.session.execute(
            select(Clue)
            .where(Clue.source_id == source_id)
            .order_by(Clue.rank.asc().nulls_last())
            .limit(limit)
        )
        return result.scalars().all()

    async def count_by_source(self, source_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Clue)
            .where(Clue.source_id == source_id)
        )
        return result.scalar_one()

    async def count_total(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Clue)
        )
        return result.scalar_one()

    async def get_by_ids(self, clue_ids: list[UUID]) -> Sequence[Clue]:
        result = await self.session.execute(
            select(Clue).where(Clue.id.in_(clue_ids))
        )
        return result.scalars().all()


class DataSourceRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, DataSource)

    async def get_all_active(self) -> Sequence[DataSource]:
        result = await self.session.execute(
            select(DataSource)
            .where(DataSource.is_active == True)
            .where(DataSource.status == "active")
            .order_by(DataSource.priority.desc())
        )
        return result.scalars().all()

    async def get_by_group(self, group_id: UUID) -> Sequence[DataSource]:
        result = await self.session.execute(
            select(DataSource)
            .where(DataSource.group_id == group_id)
            .where(DataSource.is_active == True)
        )
        return result.scalars().all()


class SourceGroupRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SourceGroup)

    async def get_all_active(self) -> Sequence[SourceGroup]:
        result = await self.session.execute(
            select(SourceGroup).where(SourceGroup.is_active == True)
        )
        return result.scalars().all()
```

- [ ] **Step 7: Create repositories/outline_repo.py**

```python
"""Outline repository"""
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outline import TopicOutline, OutlineStatus
from app.repositories.base import BaseRepository


class OutlineRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, TopicOutline)

    async def create(
        self,
        title: str,
        summary: Optional[str] = None,
        urgency: str = "中",
        created_by: Optional[UUID] = None,
        **kwargs,
    ) -> TopicOutline:
        outline = TopicOutline(
            title=title,
            summary=summary,
            urgency=urgency,
            created_by=created_by,
            status=OutlineStatus.DRAFT,
            **kwargs,
        )
        self.session.add(outline)
        await self.session.flush()
        return outline

    async def update(self, outline_id: UUID, **kwargs) -> Optional[TopicOutline]:
        outline = await self.get_by_id(outline_id)
        if outline:
            for key, value in kwargs.items():
                if hasattr(outline, key) and value is not None:
                    setattr(outline, key, value)
            await self.session.flush()
        return outline
```

- [ ] **Step 8: Create repositories/article_repo.py**

```python
"""Article repository"""
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article, ArticleStatus
from app.repositories.base import BaseRepository


class ArticleRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Article)

    async def create(
        self,
        title: str,
        author_id: Optional[UUID] = None,
        outline_id: Optional[UUID] = None,
        target_word_count: int = 1600,
        urgent: bool = False,
    ) -> Article:
        article = Article(
            title=title,
            author_id=author_id,
            outline_id=outline_id,
            target_word_count=target_word_count,
            urgent=urgent,
            status=ArticleStatus.DRAFT,
            content="",
            word_count=0,
        )
        self.session.add(article)
        await self.session.flush()
        return article

    async def save(
        self,
        article_id: UUID,
        title: Optional[str] = None,
        content: Optional[str] = None,
        **kwargs,
    ) -> Optional[Article]:
        article = await self.get_by_id(article_id)
        if not article:
            return None

        if title is not None:
            article.title = title
        if content is not None:
            article.content = content
            article.word_count = len(content)
        for key, value in kwargs.items():
            if hasattr(article, key) and value is not None:
                setattr(article, key, value)

        article.last_saved_at = datetime.now(timezone.utc)
        await self.session.flush()
        return article
```

- [ ] **Step 9: Update repositories/__init__.py**

```python
"""Repositories package"""
from app.repositories.user_repo import UserRepository
from app.repositories.org_config_repo import OrgConfigRepository
from app.repositories.clue_repo import ClueRepository, DataSourceRepository, SourceGroupRepository
from app.repositories.outline_repo import OutlineRepository
from app.repositories.article_repo import ArticleRepository

__all__ = [
    "UserRepository",
    "OrgConfigRepository",
    "ClueRepository",
    "DataSourceRepository",
    "SourceGroupRepository",
    "OutlineRepository",
    "ArticleRepository",
]
```

- [ ] **Step 10: Run repository tests**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -m pytest tests/ -v
```

Expected: PASS

- [ ] **Step 11: Commit**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent
git add api-server/
git commit -m "feat: add repository layer with CRUD operations for all models"
```

---

### Task 5: Auth Service and Auth API

**Files:**
- Create: `api-server/app/services/auth_service.py`
- Create: `api-server/app/api/auth.py`
- Modify: `api-server/app/main.py` (register auth router)
- Create: `api-server/scripts/init_db.py`

- [ ] **Step 1: Write test for login endpoint**

Create `api-server/tests/test_api/test_auth.py`:

```python
"""Test auth API endpoints"""
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_login_invalid_credentials():
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "wrong"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_without_token():
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/auth/me")
    assert response.status_code == 403  # No credentials
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -m pytest tests/test_api/test_auth.py -v
```

Expected: FAIL (router not registered)

- [ ] **Step 3: Create services/auth_service.py**

```python
"""Authentication service"""
from typing import Optional
from uuid import UUID

from app.core.security import verify_password, hash_password, create_access_token
from app.core.config import settings
from app.repositories.user_repo import UserRepository
from app.models.user import User, UserRole
from app.core.exceptions import UnauthorizedException


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def authenticate(
        self, username: str, password: str
    ) -> Optional[dict]:
        user = await self.user_repo.get_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedException("Invalid username or password")
        if not user.is_active:
            raise UnauthorizedException("User account is disabled")

        token = create_access_token(data={"sub": str(user.id)})
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_HOURS * 3600,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "display_name": user.display_name,
                "role": user.role.value if isinstance(user.role, UserRole) else user.role,
            },
        }

    async def create_user(
        self,
        username: str,
        password: str,
        display_name: str = "",
        role: UserRole = UserRole.VIEWER,
    ) -> User:
        existing = await self.user_repo.get_by_username(username)
        if existing:
            raise ValueError(f"Username '{username}' already exists")
        hashed = hash_password(password)
        return await self.user_repo.create(
            username=username,
            password_hash=hashed,
            display_name=display_name,
            role=role,
        )
```

- [ ] **Step 4: Create api/auth.py**

```python
"""Auth API router"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo
from app.services.auth_service import AuthService
from app.repositories.user_repo import UserRepository
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)
    result = await auth_service.authenticate(request.username, request.password)
    return LoginResponse(**result)


@router.get("/me", response_model=UserInfo)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserInfo(**current_user)
```

- [ ] **Step 5: Register auth router in main.py**

Add to `api-server/app/main.py` after the `app = FastAPI(...)` block:

```python
from app.api.auth import router as auth_router
app.include_router(auth_router)
```

- [ ] **Step 6: Create scripts/init_db.py**

```python
"""Initialize database with default admin user"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import db_manager
from app.services.auth_service import AuthService
from app.repositories.user_repo import UserRepository
from app.models.user import UserRole


async def init():
    await db_manager.initialize()
    async with db_manager.session() as session:
        user_repo = UserRepository(session)
        auth_service = AuthService(user_repo)

        try:
            admin = await auth_service.create_user(
                username="admin",
                password="admin123",
                display_name="管理员",
                role=UserRole.ADMIN,
            )
            print(f"Created admin user: {admin.username}")
        except ValueError as e:
            print(f"Admin user already exists: {e}")

        try:
            editor = await auth_service.create_user(
                username="editor",
                password="editor123",
                display_name="编辑",
                role=UserRole.EDITOR,
            )
            print(f"Created editor user: {editor.username}")
        except ValueError as e:
            print(f"Editor user already exists: {e}")

    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(init())
```

- [ ] **Step 7: Run auth tests**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -m pytest tests/test_api/test_auth.py -v
```

Expected: PASS (401 for invalid credentials, 403 for missing token)

- [ ] **Step 8: Verify login flow manually (requires running DB)**

```bash
# Start server
uvicorn app.main:app --reload --port 8001

# In another terminal, init DB
python scripts/init_db.py

# Test login
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

Expected: Returns JWT token

- [ ] **Step 9: Commit**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent
git add api-server/
git commit -m "feat: add auth service, login API, and init_db script"
```

---

### Task 6: AI Service (Qwen API Integration)

**Files:**
- Create: `api-server/app/services/ai_service.py`
- Create: `api-server/tests/test_services/test_ai_service.py`

- [ ] **Step 1: Write test for AI service prompt building**

Create `api-server/tests/test_services/test_ai_service.py`:

```python
"""Test AI service prompt building"""
import pytest
from app.services.ai_service import AIService


def test_build_recommendation_prompt():
    service = AIService(api_key="test-key")
    prompt = service._build_recommendation_prompt(
        domains=["财经", "民生"],
        style=["客观", "严谨"],
        clues_text="1. 全球气候峰会达成协议 (热度: 5892341)\n2. 房贷利率再下调 (热度: 4215678)",
    )
    assert "财经" in prompt
    assert "客观" in prompt
    assert "全球气候峰会" in prompt


def test_build_outline_prompt():
    service = AIService(api_key="test-key")
    prompt = service._build_outline_prompt(
        domains=["财经", "民生"],
        style=["客观", "严谨"],
        clues_text="线索内容...",
        additional_context="关注政策影响",
    )
    assert "财经" in prompt
    assert "关注政策影响" in prompt
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -m pytest tests/test_services/test_ai_service.py -v
```

Expected: FAIL

- [ ] **Step 3: Create services/ai_service.py**

```python
"""AI service — Alibaba Cloud Bailian (Qwen) integration"""
import json
import hashlib
from typing import Optional

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.exceptions import (
    AIServiceError,
    AIServiceTimeoutError,
    AIServiceRateLimitError,
    AIServiceContentError,
)
from app.utils.cache import cache_manager

logger = structlog.get_logger("ai_service")


class AIService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.QWEN_API_KEY
        self.model = model or settings.QWEN_MODEL
        self.base_url = settings.QWEN_BASE_URL
        self.timeout = settings.QWEN_TIMEOUT

    # --- Public methods ---

    async def generate_topic_recommendations(
        self,
        domains: list[str],
        style: list[str],
        clues_text: str,
        limit: int = 5,
    ) -> list[dict]:
        cache_key = self._cache_key("recommendations", domains, style, clues_text[:200])
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached

        prompt = self._build_recommendation_prompt(domains, style, clues_text)
        response = await self._call_qwen(prompt)
        result = self._parse_json_list(response, limit)

        await cache_manager.set(cache_key, result, ttl=settings.AI_CACHE_TTL)
        return result

    async def generate_outline(
        self,
        domains: list[str],
        style: list[str],
        clues_text: str,
        additional_context: Optional[str] = None,
    ) -> dict:
        prompt = self._build_outline_prompt(domains, style, clues_text, additional_context)
        response = await self._call_qwen(prompt)
        return self._parse_json_dict(response)

    async def generate_headlines(
        self,
        outline_text: str,
        styles: list[str] | None = None,
    ) -> list[dict]:
        styles = styles or ["硬核新闻风", "叙事分析风", "深度解读风"]
        prompt = self._build_headlines_prompt(outline_text, styles)
        response = await self._call_qwen(prompt)
        return self._parse_json_list(response, 3)

    async def generate_writing_suggestions(
        self,
        title: str,
        content: str,
    ) -> list[dict]:
        prompt = self._build_writing_suggestions_prompt(title, content)
        response = await self._call_qwen(prompt)
        return self._parse_json_list(response, 5)

    async def analyze_content_metrics(
        self,
        content: str,
    ) -> dict:
        prompt = self._build_metrics_prompt(content)
        response = await self._call_qwen(prompt)
        return self._parse_json_dict(response)

    # --- Prompt builders ---

    def _build_recommendation_prompt(
        self, domains: list[str], style: list[str], clues_text: str
    ) -> str:
        return f"""你是一位资深媒体选题顾问。请根据以下信息，推荐 5 个值得深入报道的选题。

## 组织定位
- 关注领域：{', '.join(domains)}
- 报道风格：{', '.join(style)}

## 最新线索数据
{clues_text}

## 输出要求
以 JSON 数组格式输出，每个元素包含：
- source: 来源平台
- source_icon: 图标类型(newspaper/flame/trending-up)
- tag: 分类标签
- title: 选题标题（简洁有力）
- reason: 推荐理由
- angles: 切入角度数组（2-3个）

请直接输出 JSON 数组，不要包含其他文字。"""

    def _build_outline_prompt(
        self,
        domains: list[str],
        style: list[str],
        clues_text: str,
        additional_context: Optional[str] = None,
    ) -> str:
        context_section = f"\n## 补充说明\n{additional_context}" if additional_context else ""
        return f"""你是一位资深媒体选题策划师。请根据以下线索，生成完整的选题大纲。

## 组织定位
- 关注领域：{', '.join(domains)}
- 报道风格：{', '.join(style)}
{context_section}

## 线索详情
{clues_text}

## 输出要求
以 JSON 对象格式输出，包含以下字段：
- summary: 概要描述（100字内）
- urgency: 紧急程度（高/中/低）
- info_density: 信息密度评分（0-100整数）
- headlines: 标题建议数组，每个元素包含 style 和 text
- lead_paragraph: 导语段落（200字内）
- outline_sections: 大纲结构数组，每个元素包含 id, number, title, items(数组，每个含 id, content, has_ai_rewrite)
- interview_directions: 采访方向数组，每个含 id, role, description
- references: 参考资料数组，每个含 id, title, source, url

请直接输出 JSON 对象，不要包含其他文字。"""

    def _build_headlines_prompt(self, outline_text: str, styles: list[str]) -> str:
        styles_str = "、".join(styles)
        return f"""请为以下选题内容生成 3 个不同风格的标题建议。

## 选题内容
{outline_text}

## 需要的风格
{styles_str}

以 JSON 数组输出，每个元素包含 style 和 text。直接输出 JSON。"""

    def _build_writing_suggestions_prompt(self, title: str, content: str) -> str:
        return f"""你是一位资深新闻编辑。请阅读以下文章，提供写作改进建议。

## 文章标题
{title}

## 文章内容
{content}

以 JSON 数组输出，每个元素包含：
- type: 类型(grammar/style/fact)
- original: 原文片段
- suggested: 建议修改
- reason: 理由

最多提供 5 条建议。直接输出 JSON。"""

    def _build_metrics_prompt(self, content: str) -> str:
        return f"""请分析以下新闻文章的客观性和可读性。

## 文章内容
{content}

以 JSON 对象输出：
- objectivity: 客观性评分（0-100整数）
- readability: 可读性等级（如 A1, A2, B1, B2, C1, C2）

直接输出 JSON。"""

    # --- API call ---

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=5, max=30),
        reraise=True,
    )
    async def _call_qwen(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": {"prompt": prompt},
            "parameters": {"result_format": "text"},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.base_url, headers=headers, json=payload
                )

                if response.status_code == 429:
                    raise AIServiceRateLimitError("Qwen API rate limit exceeded")
                if response.status_code == 400:
                    raise AIServiceContentError(f"Content error: {response.text}")

                response.raise_for_status()
                data = response.json()
                return data["output"]["text"]

        except httpx.TimeoutException:
            raise AIServiceTimeoutError("Qwen API timeout")
        except httpx.HTTPStatusError as e:
            raise AIServiceError(f"Qwen API error: {e}")
        except (AIServiceRateLimitError, AIServiceTimeoutError, AIServiceContentError):
            raise
        except Exception as e:
            raise AIServiceError(f"Unexpected error: {e}")

    # --- Helpers ---

    def _parse_json_list(self, text: str, limit: int = 10) -> list[dict]:
        try:
            result = json.loads(text)
            if isinstance(result, list):
                return result[:limit]
            if isinstance(result, dict) and "items" in result:
                return result["items"][:limit]
            return [result][:limit]
        except json.JSONDecodeError:
            logger.error("ai_json_parse_error", text=text[:200])
            return []

    def _parse_json_dict(self, text: str) -> dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.error("ai_json_parse_error", text=text[:200])
            return {}

    def _cache_key(self, prefix: str, *args) -> str:
        content = ":".join(str(a) for a in args)
        hash_val = hashlib.md5(content.encode()).hexdigest()
        return f"ai:{prefix}:{hash_val}"
```

- [ ] **Step 4: Run AI service tests**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -m pytest tests/test_services/test_ai_service.py -v
```

Expected: PASS (tests only prompt building, no API calls)

- [ ] **Step 5: Commit**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent
git add api-server/
git commit -m "feat: add AI service with Qwen API integration and prompt templates"
```

---

### Task 7: Dashboard Service and API

**Files:**
- Create: `api-server/app/services/dashboard_service.py`
- Create: `api-server/app/api/dashboard.py`
- Modify: `api-server/app/main.py` (register dashboard router)

- [ ] **Step 1: Write test for dashboard endpoint**

Create `api-server/tests/test_api/test_dashboard.py`:

```python
"""Test dashboard API endpoint"""
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_dashboard_requires_auth():
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/dashboard")
    assert response.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -m pytest tests/test_api/test_dashboard.py -v
```

Expected: FAIL (router not registered)

- [ ] **Step 3: Create services/dashboard_service.py**

```python
"""Dashboard data aggregation service"""
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.clue_repo import ClueRepository, DataSourceRepository, SourceGroupRepository
from app.services.ai_service import AIService
from app.utils.cache import cache_manager
from app.core.config import settings
import structlog

logger = structlog.get_logger("dashboard_service")

# Platform display labels
PLATFORM_LABELS = {
    "weibo": "微博热搜",
    "douyin": "抖音热榜",
    "zhihu": "知乎热榜",
    "baidu": "百度热搜",
    "bilibili": "B站热门",
    "toutiao": "今日头条",
}

STATUS_MAP = {
    "new": "new",
    "up": "rank_up",
    "down": "rank_down",
    "stable": "stable",
    "explosive": "explosive",
}


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.clue_repo = ClueRepository(db)
        self.source_repo = DataSourceRepository(db)
        self.group_repo = SourceGroupRepository(db)

    async def get_dashboard_data(self, org_config: Optional[dict] = None) -> dict:
        cache_key = "dashboard:data"
        cached = await cache_manager.get(cache_key)
        if cached:
            return cached

        trending_cards = await self._build_trending_cards()
        kol_columns = await self._build_kol_columns()
        ai_suggestions = await self._build_ai_suggestions(org_config)
        stats = await self._build_stats()

        result = {
            "trending_cards": trending_cards,
            "kol_columns": kol_columns,
            "ai_suggestions": ai_suggestions,
            "active_threads": stats["active_threads"],
            "topic_alerts": stats["topic_alerts"],
            "quote": stats["quote"],
        }

        await cache_manager.set(cache_key, result, ttl=60)
        return result

    async def _build_trending_cards(self) -> list[dict]:
        sources = await self.source_repo.get_all_active()
        cards = []
        for source in sources:
            platform = source.config.get("platform", source.name.lower()) if isinstance(source.config, dict) else source.name.lower()
            clues = await self.clue_repo.get_hot_by_source(source.id, limit=10)

            items = []
            for clue in clues:
                status = "stable"
                if clue.rank and clue.rank <= 3:
                    status = "explosive"
                items.append({
                    "id": str(clue.id),
                    "rank": clue.rank or 0,
                    "title": clue.title,
                    "heat_value": clue.heat_value or "",
                    "status": status,
                    "url": clue.url,
                })

            if items:
                cards.append({
                    "platform": platform,
                    "platform_label": PLATFORM_LABELS.get(platform, source.name),
                    "items": items,
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                })

        return cards

    async def _build_kol_columns(self) -> list[dict]:
        # KOL data comes from account-type data sources
        sources = await self.source_repo.get_all_active()
        kol_sources = [s for s in sources if s.type == "account"]
        columns = []
        for source in kol_sources:
            clues = await self.clue_repo.get_latest_by_source(source.id, limit=5)
            posts = []
            for clue in clues:
                posts.append({
                    "id": str(clue.id),
                    "author": clue.author or source.name,
                    "verified": True,
                    "content": clue.title,
                    "likes": clue.likes or 0,
                    "shares": clue.shares or 0,
                    "comments": clue.comments or 0,
                    "time_ago": "",
                })
            if posts:
                columns.append({
                    "platform": source.config.get("platform", "weibo") if isinstance(source.config, dict) else "weibo",
                    "platform_label": f"{source.name} KOL",
                    "posts": posts,
                })
        return columns

    async def _build_ai_suggestions(self, org_config: Optional[dict]) -> list[dict]:
        if not org_config:
            return []
        try:
            ai_service = AIService()
            clues = await self.clue_repo.get_all(limit=50)
            clues_text = "\n".join(
                f"{i+1}. {c.title} (热度: {c.heat_value or 'N/A'})"
                for i, c in enumerate(clues[:20])
            )
            recommendations = await ai_service.generate_topic_recommendations(
                domains=org_config.get("domains", []),
                style=org_config.get("style", []),
                clues_text=clues_text,
                limit=2,
            )
            return [
                {
                    "id": f"ai{i+1}",
                    "title": r.get("title", ""),
                    "description": r.get("reason", ""),
                }
                for i, r in enumerate(recommendations)
            ]
        except Exception as e:
            logger.error("dashboard_ai_suggestions_failed", error=str(e))
            return []

    async def _build_stats(self) -> dict:
        total_clues = await self.clue_repo.count_total()
        return {
            "active_threads": total_clues,
            "topic_alerts": min(total_clues // 1000, 50),
            "quote": {
                "text": "权威性来源于数据的密度与筛选的精准度。",
                "source": "AI 洞察",
            },
        }
```

- [ ] **Step 4: Create api/dashboard.py**

```python
"""Dashboard API router"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.dashboard_service import DashboardService
from app.repositories.org_config_repo import OrgConfigRepository
from app.schemas.dashboard import DashboardData

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_config_repo = OrgConfigRepository(db)
    org_config = await org_config_repo.get_active()
    org_config_dict = None
    if org_config:
        org_config_dict = {
            "domains": org_config.domains,
            "style": org_config.style,
        }

    service = DashboardService(db)
    data = await service.get_dashboard_data(org_config_dict)
    return DashboardData(**data)
```

- [ ] **Step 5: Register dashboard router in main.py**

Add to `api-server/app/main.py`:

```python
from app.api.dashboard import router as dashboard_router
app.include_router(dashboard_router)
```

- [ ] **Step 6: Run tests**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -m pytest tests/test_api/test_dashboard.py -v
```

Expected: PASS

- [ ] **Step 7: Commit**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent
git add api-server/
git commit -m "feat: add dashboard service and API endpoint"
```

---

### Task 8: Discovery Service and API

**Files:**
- Create: `api-server/app/services/discovery_service.py`
- Create: `api-server/app/api/discovery.py`
- Modify: `api-server/app/main.py` (register discovery router)

- [ ] **Step 1: Write test for discovery endpoints**

Create `api-server/tests/test_api/test_discovery.py`:

```python
"""Test discovery API endpoints"""
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_discovery_requires_auth():
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/discovery")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_discovery_config_requires_auth():
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/discovery/config")
    assert response.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -m pytest tests/test_api/test_discovery.py -v
```

Expected: FAIL

- [ ] **Step 3: Create services/discovery_service.py**

```python
"""AI Discovery service"""
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.org_config_repo import OrgConfigRepository
from app.repositories.clue_repo import ClueRepository
from app.services.ai_service import AIService
from app.utils.cache import cache_manager
import structlog

logger = structlog.get_logger("discovery_service")


class DiscoveryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.org_config_repo = OrgConfigRepository(db)
        self.clue_repo = ClueRepository(db)
        self.ai_service = AIService()

    async def get_config(self) -> Optional[dict]:
        config = await self.org_config_repo.get_active()
        if not config:
            return None
        return {
            "id": str(config.id),
            "name": config.name,
            "domains": config.domains,
            "style": config.style,
        }

    async def update_config(self, name: Optional[str], domains: Optional[list], style: Optional[list]) -> dict:
        active = await self.org_config_repo.get_active()
        config_name = name or (active.name if active else "Default")
        config_domains = domains or (active.domains if active else [])
        config_style = style or (active.style if active else [])

        config = await self.org_config_repo.create_or_update(
            name=config_name,
            domains=config_domains,
            style=config_style,
        )
        # Invalidate cached recommendations
        await cache_manager.delete("discovery:recommendations")
        return {
            "id": str(config.id),
            "name": config.name,
            "domains": config.domains,
            "style": config.style,
        }

    async def get_recommendations(self, force_refresh: bool = False) -> dict:
        cache_key = "discovery:recommendations"

        if not force_refresh:
            cached = await cache_manager.get(cache_key)
            if cached:
                return cached

        org_config = await self.org_config_repo.get_active()
        if not org_config:
            return {
                "org_config": {"id": "", "name": "", "domains": [], "style": []},
                "total_clues": 0,
                "last_updated": "",
                "recommendations": [],
                "total_recommendations": 0,
            }

        total_clues = await self.clue_repo.count_total()
        clues = await self.clue_repo.get_all(limit=50)

        clues_text = "\n".join(
            f"{i+1}. [{c.author or '未知'}] {c.title} (热度: {c.heat_value or 'N/A'})"
            for i, c in enumerate(clues[:30])
        )

        try:
            raw_recommendations = await self.ai_service.generate_topic_recommendations(
                domains=org_config.domains,
                style=org_config.style,
                clues_text=clues_text,
                limit=10,
            )
        except Exception as e:
            logger.error("discovery_ai_failed", error=str(e))
            raw_recommendations = []

        recommendations = []
        for i, r in enumerate(raw_recommendations):
            recommendations.append({
                "id": f"rec{i+1}",
                "source": r.get("source", ""),
                "source_icon": r.get("source_icon", "newspaper"),
                "tag": r.get("tag", ""),
                "title": r.get("title", ""),
                "reason": r.get("reason", ""),
                "angles": r.get("angles", []),
            })

        result = {
            "org_config": {
                "id": str(org_config.id),
                "name": org_config.name,
                "domains": org_config.domains,
                "style": org_config.style,
            },
            "total_clues": total_clues,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
        }

        await cache_manager.set(cache_key, result, ttl=300)
        return result
```

- [ ] **Step 4: Create api/discovery.py**

```python
"""Discovery API router"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.discovery_service import DiscoveryService
from app.schemas.discovery import (
    DiscoveryResponse,
    OrgConfigResponse,
    OrgConfigUpdate,
)

router = APIRouter(prefix="/api/discovery", tags=["discovery"])


@router.get("/config", response_model=OrgConfigResponse)
async def get_config(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DiscoveryService(db)
    config = await service.get_config()
    if not config:
        return OrgConfigResponse(id="", name="", domains=[], style=[])
    return OrgConfigResponse(**config)


@router.put("/config", response_model=OrgConfigResponse)
async def update_config(
    request: OrgConfigUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DiscoveryService(db)
    config = await service.update_config(
        name=request.name,
        domains=request.domains,
        style=request.style,
    )
    return OrgConfigResponse(**config)


@router.get("", response_model=DiscoveryResponse)
async def get_discovery(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DiscoveryService(db)
    return await service.get_recommendations()


@router.post("/refresh", response_model=DiscoveryResponse)
async def refresh_discovery(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DiscoveryService(db)
    return await service.get_recommendations(force_refresh=True)
```

- [ ] **Step 5: Register discovery router in main.py**

Add to `api-server/app/main.py`:

```python
from app.api.discovery import router as discovery_router
app.include_router(discovery_router)
```

- [ ] **Step 6: Run tests**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -m pytest tests/test_api/test_discovery.py -v
```

Expected: PASS

- [ ] **Step 7: Commit**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent
git add api-server/
git commit -m "feat: add AI Discovery service and API endpoints"
```

---

### Task 9: Outlines Service and API

**Files:**
- Create: `api-server/app/services/outlines_service.py`
- Create: `api-server/app/api/outlines.py`
- Modify: `api-server/app/main.py` (register outlines router)

- [ ] **Step 1: Write test for outlines endpoints**

Create `api-server/tests/test_api/test_outlines.py`:

```python
"""Test outlines API endpoints"""
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_outlines_list_requires_auth():
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/outlines")
    assert response.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -m pytest tests/test_api/test_outlines.py -v
```

Expected: FAIL

- [ ] **Step 3: Create services/outlines_service.py**

```python
"""Outlines service"""
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.outline_repo import OutlineRepository
from app.repositories.clue_repo import ClueRepository
from app.repositories.org_config_repo import OrgConfigRepository
from app.services.ai_service import AIService
from app.models.outline import TopicOutline
import structlog

logger = structlog.get_logger("outlines_service")


class OutlinesService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.outline_repo = OutlineRepository(db)
        self.clue_repo = ClueRepository(db)
        self.org_config_repo = OrgConfigRepository(db)
        self.ai_service = AIService()

    async def list_outlines(self, page: int = 1, page_size: int = 20) -> dict:
        offset = (page - 1) * page_size
        items = await self.outline_repo.get_all(limit=page_size, offset=offset)
        total = await self.outline_repo.count()
        return {
            "total": total,
            "items": [self._format_outline(o) for o in items],
        }

    async def get_outline(self, outline_id: UUID) -> Optional[dict]:
        outline = await self.outline_repo.get_by_id(outline_id)
        if not outline:
            return None
        return self._format_outline(outline)

    async def create_outline(self, title: str, summary: Optional[str], urgency: str, user_id: UUID) -> dict:
        outline = await self.outline_repo.create(
            title=title,
            summary=summary,
            urgency=urgency,
            created_by=user_id,
        )
        return self._format_outline(outline)

    async def update_outline(self, outline_id: UUID, **kwargs) -> Optional[dict]:
        outline = await self.outline_repo.update(outline_id, **kwargs)
        if not outline:
            return None
        return self._format_outline(outline)

    async def delete_outline(self, outline_id: UUID) -> bool:
        return await self.outline_repo.delete_by_id(outline_id)

    async def generate_from_clues(
        self,
        clue_ids: list[str],
        additional_context: Optional[str],
        user_id: UUID,
    ) -> dict:
        # Fetch clues
        uuid_ids = [UUID(cid) for cid in clue_ids]
        clues = await self.clue_repo.get_by_ids(uuid_ids)
        clues_text = "\n".join(
            f"- [{c.author or '未知'}] {c.title} (热度: {c.heat_value or 'N/A'}, 链接: {c.url or '无'})"
            for c in clues
        )

        # Get org config
        org_config = await self.org_config_repo.get_active()
        domains = org_config.domains if org_config else []
        style = org_config.style if org_config else []

        # Generate via AI
        ai_result = await self.ai_service.generate_outline(
            domains=domains,
            style=style,
            clues_text=clues_text,
            additional_context=additional_context,
        )

        # Create outline record
        outline = await self.outline_repo.create(
            title=ai_result.get("title", "未命名选题"),
            summary=ai_result.get("summary"),
            urgency=ai_result.get("urgency", "中"),
            info_density=ai_result.get("info_density", 0),
            headlines=ai_result.get("headlines"),
            lead_paragraph=ai_result.get("lead_paragraph"),
            outline_sections=ai_result.get("outline_sections"),
            interview_directions=ai_result.get("interview_directions"),
            references=ai_result.get("references"),
            source_clue_ids=clue_ids,
            ai_model=self.ai_service.model,
            created_by=user_id,
        )
        return self._format_outline(outline)

    async def regenerate_section(
        self,
        outline_id: UUID,
        section: str,
    ) -> Optional[dict]:
        outline = await self.outline_repo.get_by_id(outline_id)
        if not outline:
            return None

        outline_text = f"标题: {outline.title}\n概要: {outline.summary or ''}"

        if section == "headlines":
            headlines = await self.ai_service.generate_headlines(outline_text)
            await self.outline_repo.update(outline_id, headlines=headlines)
        elif section == "outline":
            # Re-generate outline sections
            org_config = await self.org_config_repo.get_active()
            domains = org_config.domains if org_config else []
            style = org_config.style if org_config else []
            clues_text = outline.summary or outline.title
            ai_result = await self.ai_service.generate_outline(domains, style, clues_text)
            await self.outline_repo.update(
                outline_id,
                outline_sections=ai_result.get("outline_sections"),
            )
        elif section == "interview":
            interview = await self.ai_service.generate_headlines(
                f"采访方向生成\n{outline_text}\n概要: {outline.summary}",
                styles=["政策观察家", "一线从业者", "学术研究者"],
            )
            directions = [
                {"id": f"i{i+1}", "role": h.get("style", ""), "description": h.get("text", "")}
                for i, h in enumerate(interview)
            ]
            await self.outline_repo.update(outline_id, interview_directions=directions)

        updated = await self.outline_repo.get_by_id(outline_id)
        return self._format_outline(updated)

    def _format_outline(self, outline: TopicOutline) -> dict:
        return {
            "id": str(outline.id),
            "title": outline.title,
            "summary": outline.summary,
            "urgency": outline.urgency,
            "info_density": outline.info_density,
            "headlines": outline.headlines,
            "lead_paragraph": outline.lead_paragraph,
            "outline_sections": outline.outline_sections,
            "interview_directions": outline.interview_directions,
            "references": outline.references,
            "source_clue_ids": outline.source_clue_ids,
            "ai_model": outline.ai_model,
            "status": outline.status,
            "created_at": outline.created_at,
            "updated_at": outline.updated_at,
        }
```

- [ ] **Step 4: Create api/outlines.py**

```python
"""Outlines API router"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.outlines_service import OutlinesService
from app.schemas.outlines import (
    OutlineListResponse,
    OutlineResponse,
    OutlineCreateRequest,
    OutlineUpdateRequest,
    OutlineGenerateRequest,
    OutlineRegenerateRequest,
)
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/api/outlines", tags=["outlines"])


@router.get("", response_model=OutlineListResponse)
async def list_outlines(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OutlinesService(db)
    return await service.list_outlines(page, page_size)


@router.get("/{outline_id}", response_model=OutlineResponse)
async def get_outline(
    outline_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OutlinesService(db)
    result = await service.get_outline(outline_id)
    if not result:
        raise NotFoundException("Outline not found")
    return result


@router.post("", response_model=OutlineResponse)
async def create_outline(
    request: OutlineCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OutlinesService(db)
    return await service.create_outline(
        title=request.title,
        summary=request.summary,
        urgency=request.urgency,
        user_id=UUID(current_user["id"]),
    )


@router.put("/{outline_id}", response_model=OutlineResponse)
async def update_outline(
    outline_id: UUID,
    request: OutlineUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OutlinesService(db)
    result = await service.update_outline(outline_id, **request.model_dump(exclude_none=True))
    if not result:
        raise NotFoundException("Outline not found")
    return result


@router.delete("/{outline_id}")
async def delete_outline(
    outline_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OutlinesService(db)
    deleted = await service.delete_outline(outline_id)
    if not deleted:
        raise NotFoundException("Outline not found")
    return {"detail": "Deleted"}


@router.post("/generate", response_model=OutlineResponse)
async def generate_outline(
    request: OutlineGenerateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OutlinesService(db)
    return await service.generate_from_clues(
        clue_ids=request.clue_ids,
        additional_context=request.additional_context,
        user_id=UUID(current_user["id"]),
    )


@router.post("/{outline_id}/regenerate", response_model=OutlineResponse)
async def regenerate_section(
    outline_id: UUID,
    request: OutlineRegenerateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OutlinesService(db)
    result = await service.regenerate_section(outline_id, request.section)
    if not result:
        raise NotFoundException("Outline not found")
    return result
```

- [ ] **Step 5: Register outlines router in main.py**

Add to `api-server/app/main.py`:

```python
from app.api.outlines import router as outlines_router
app.include_router(outlines_router)
```

- [ ] **Step 6: Run tests**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -m pytest tests/test_api/test_outlines.py -v
```

Expected: PASS

- [ ] **Step 7: Commit**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent
git add api-server/
git commit -m "feat: add outlines service, CRUD API, and AI generation endpoints"
```

---

### Task 10: Workbench Service and API

**Files:**
- Create: `api-server/app/services/workbench_service.py`
- Create: `api-server/app/api/workbench.py`
- Modify: `api-server/app/main.py` (register workbench router)

- [ ] **Step 1: Write test for workbench endpoints**

Create `api-server/tests/test_api/test_workbench.py`:

```python
"""Test workbench API endpoints"""
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_workbench_articles_requires_auth():
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/workbench/articles")
    assert response.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -m pytest tests/test_api/test_workbench.py -v
```

Expected: FAIL

- [ ] **Step 3: Create services/workbench_service.py**

```python
"""Workbench service — article management and AI assistance"""
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.article_repo import ArticleRepository
from app.services.ai_service import AIService
from app.models.article import Article
from app.core.exceptions import NotFoundException
import structlog

logger = structlog.get_logger("workbench_service")


class WorkbenchService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.article_repo = ArticleRepository(db)
        self.ai_service = AIService()

    async def list_articles(self, page: int = 1, page_size: int = 20) -> dict:
        offset = (page - 1) * page_size
        items = await self.article_repo.get_all(limit=page_size, offset=offset)
        total = await self.article_repo.count()
        return {
            "total": total,
            "items": [self._format_article(a) for a in items],
        }

    async def get_article(self, article_id: UUID) -> Optional[dict]:
        article = await self.article_repo.get_by_id(article_id)
        if not article:
            return None
        return self._format_article(article)

    async def create_article(
        self,
        title: str,
        author_id: Optional[UUID],
        outline_id: Optional[UUID],
        target_word_count: int,
        urgent: bool,
    ) -> dict:
        article = await self.article_repo.create(
            title=title,
            author_id=author_id,
            outline_id=outline_id,
            target_word_count=target_word_count,
            urgent=urgent,
        )
        return self._format_article(article)

    async def save_article(self, article_id: UUID, **kwargs) -> Optional[dict]:
        article = await self.article_repo.save(article_id, **kwargs)
        if not article:
            return None
        return self._format_article(article)

    async def delete_article(self, article_id: UUID) -> bool:
        return await self.article_repo.delete_by_id(article_id)

    async def ai_suggest(self, article_id: UUID) -> Optional[dict]:
        article = await self.article_repo.get_by_id(article_id)
        if not article:
            return None

        try:
            suggestions = await self.ai_service.generate_writing_suggestions(
                title=article.title,
                content=article.content or "",
            )
            formatted = [
                {
                    "id": f"sug{i+1}",
                    "type": s.get("type", "style"),
                    "original": s.get("original", ""),
                    "suggested": s.get("suggested", ""),
                    "reason": s.get("reason", ""),
                }
                for i, s in enumerate(suggestions)
            ]
            # Save suggestions to article
            await self.article_repo.save(article_id, ai_suggestions=formatted)
            return {"ai_suggestions": formatted}
        except Exception as e:
            logger.error("workbench_ai_suggest_failed", error=str(e))
            return {"ai_suggestions": []}

    async def ai_metrics(self, article_id: UUID) -> Optional[dict]:
        article = await self.article_repo.get_by_id(article_id)
        if not article:
            return None

        try:
            metrics = await self.ai_service.analyze_content_metrics(
                content=article.content or "",
            )
            formatted = {
                "objectivity": metrics.get("objectivity", 0),
                "readability": metrics.get("readability", ""),
            }
            await self.article_repo.save(article_id, metrics=formatted)
            return {"metrics": formatted}
        except Exception as e:
            logger.error("workbench_ai_metrics_failed", error=str(e))
            return {"metrics": {"objectivity": 0, "readability": ""}}

    def _format_article(self, article: Article) -> dict:
        completion = 0
        if article.target_word_count > 0:
            completion = min(int(article.word_count / article.target_word_count * 100), 100)

        return {
            "id": str(article.id),
            "outline_id": str(article.outline_id) if article.outline_id else None,
            "title": article.title,
            "author_id": str(article.author_id) if article.author_id else None,
            "content": article.content,
            "word_count": article.word_count,
            "target_word_count": article.target_word_count,
            "completion_percent": completion,
            "urgent": article.urgent,
            "ai_suggestions": article.ai_suggestions,
            "metrics": article.metrics,
            "references": article.references,
            "status": article.status,
            "last_saved_at": article.last_saved_at,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
        }
```

- [ ] **Step 4: Create api/workbench.py**

```python
"""Workbench API router"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.workbench_service import WorkbenchService
from app.schemas.workbench import (
    ArticleListResponse,
    ArticleResponse,
    ArticleCreateRequest,
    ArticleUpdateRequest,
)
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/api/workbench", tags=["workbench"])


@router.get("/articles", response_model=ArticleListResponse)
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkbenchService(db)
    return await service.list_articles(page, page_size)


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkbenchService(db)
    result = await service.get_article(article_id)
    if not result:
        raise NotFoundException("Article not found")
    return result


@router.post("/articles", response_model=ArticleResponse)
async def create_article(
    request: ArticleCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkbenchService(db)
    return await service.create_article(
        title=request.title,
        author_id=UUID(current_user["id"]),
        outline_id=UUID(request.outline_id) if request.outline_id else None,
        target_word_count=request.target_word_count,
        urgent=request.urgent,
    )


@router.put("/articles/{article_id}", response_model=ArticleResponse)
async def save_article(
    article_id: UUID,
    request: ArticleUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkbenchService(db)
    result = await service.save_article(
        article_id, **request.model_dump(exclude_none=True)
    )
    if not result:
        raise NotFoundException("Article not found")
    return result


@router.delete("/articles/{article_id}")
async def delete_article(
    article_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkbenchService(db)
    deleted = await service.delete_article(article_id)
    if not deleted:
        raise NotFoundException("Article not found")
    return {"detail": "Deleted"}


@router.post("/articles/{article_id}/ai-suggest")
async def ai_suggest(
    article_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkbenchService(db)
    result = await service.ai_suggest(article_id)
    if result is None:
        raise NotFoundException("Article not found")
    return result


@router.post("/articles/{article_id}/ai-metrics")
async def ai_metrics(
    article_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkbenchService(db)
    result = await service.ai_metrics(article_id)
    if result is None:
        raise NotFoundException("Article not found")
    return result
```

- [ ] **Step 5: Register workbench router in main.py**

Add to `api-server/app/main.py`:

```python
from app.api.workbench import router as workbench_router
app.include_router(workbench_router)
```

- [ ] **Step 6: Run tests**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -m pytest tests/test_api/test_workbench.py -v
```

Expected: PASS

- [ ] **Step 7: Commit**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent
git add api-server/
git commit -m "feat: add workbench service, article CRUD, and AI suggestion endpoints"
```

---

### Task 11: Docker Configuration and Docker Compose Merge

**Files:**
- Create: `api-server/docker/Dockerfile`
- Create: `api-server/docker/docker-compose.yml`
- Create: `api-server/scripts/seed_data.py`

- [ ] **Step 1: Create docker/Dockerfile**

```dockerfile
FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY migrations/ ./migrations/
COPY scripts/ ./scripts/
COPY alembic.ini .

CMD ["sh", "-c", "alembic upgrade head && python scripts/init_db.py && uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT:-8001}"]
```

- [ ] **Step 2: Create docker/docker-compose.yml**

```yaml
services:
  api-server:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: api-server
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/clue_collector
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=dev-secret-key-change-in-prod
      - QWEN_API_KEY=${QWEN_API_KEY}
      - APP_PORT=8001
      - APP_ENV=development
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - clue-collector-network
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    container_name: clue-collector-postgres
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=clue_collector
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - clue-collector-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d clue_collector"]
      interval: 5s
      timeout: 5s
      retries: 10
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: clue-collector-redis
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"
    networks:
      - clue-collector-network
    restart: unless-stopped

volumes:
  postgres-data:
  redis-data:

networks:
  clue-collector-network:
    driver: bridge
```

- [ ] **Step 3: Create scripts/seed_data.py**

```python
"""Seed demo data for development"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import db_manager
from app.repositories.org_config_repo import OrgConfigRepository


async def seed():
    await db_manager.initialize()
    async with db_manager.session() as session:
        # Create default org config
        org_repo = OrgConfigRepository(session)
        config = await org_repo.create_or_update(
            name="默认媒体机构",
            domains=["财经", "民生", "科技"],
            style=["客观", "严谨", "深度"],
        )
        print(f"Created org config: {config.name}")

    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(seed())
```

- [ ] **Step 4: Verify Docker build**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server/docker
docker compose build
```

Expected: Build succeeds

- [ ] **Step 5: Commit**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent
git add api-server/
git commit -m "feat: add Docker configuration and seed data script"
```

---

### Task 12: Frontend API Client Update

**Files:**
- Modify: `web/src/lib/api/client.ts`

- [ ] **Step 1: Update client.ts to support JWT auth**

Replace `web/src/lib/api/client.ts` with:

```typescript
import { dashboardData } from "@/lib/mock/dashboard";
import { aiDiscoveryData } from "@/lib/mock/ai-discovery";
import { outlinesData } from "@/lib/mock/outlines";
import { workbenchData } from "@/lib/mock/workbench";

const USE_MOCK = !process.env.NEXT_PUBLIC_API_URL;

const mockDataMap: Record<string, unknown> = {
  "/api/dashboard": dashboardData,
  "/api/discovery": aiDiscoveryData,
  "/api/outlines": outlinesData,
  "/api/workbench": workbenchData,
};

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setToken(token: string): void {
  localStorage.setItem("access_token", token);
}

export function clearToken(): void {
  localStorage.removeItem("access_token");
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export async function fetchFromApi<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 200));
    const data = mockDataMap[path];
    if (!data) throw new Error(`No mock data for ${path}`);
    return data as T;
  }

  const baseUrl = process.env.NEXT_PUBLIC_API_URL!;
  const token = getToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }

  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<T>;
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/web
npx tsc --noEmit
```

Expected: No errors (or only pre-existing errors)

- [ ] **Step 3: Commit**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent
git add web/src/lib/api/client.ts
git commit -m "feat: add JWT auth support to frontend API client"
```

---

### Task 13: Integration Smoke Test

**Files:**
- Create: `api-server/tests/conftest.py`

- [ ] **Step 1: Create test conftest with fixtures**

Create `api-server/tests/conftest.py`:

```python
"""Test configuration and fixtures"""
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def client():
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def auth_token(client: AsyncClient):
    """Get auth token for protected endpoints (requires running DB with init_db)"""
    # This will only work with a running database
    # In CI, use test database with seed data
    response = await client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None
```

- [ ] **Step 2: Create integration smoke test**

Create `api-server/tests/test_integration.py`:

```python
"""Integration smoke test — verifies all routers are registered"""
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_all_routes_registered():
    """Verify all expected routes are accessible (will return 403 for auth-required routes)"""
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Auth routes
        r = await client.post("/api/auth/login", json={"username": "x", "password": "x"})
        assert r.status_code in (401, 422)

        r = await client.get("/api/auth/me")
        assert r.status_code == 403

        # Protected routes (should return 403 without token)
        r = await client.get("/api/dashboard")
        assert r.status_code == 403

        r = await client.get("/api/discovery")
        assert r.status_code == 403

        r = await client.get("/api/outlines")
        assert r.status_code == 403

        r = await client.get("/api/workbench/articles")
        assert r.status_code == 403
```

- [ ] **Step 3: Run integration smoke test**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -m pytest tests/test_integration.py -v
```

Expected: PASS — all routes respond (403 for protected, 401 for invalid login)

- [ ] **Step 4: Run full test suite**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent/api-server
source venv/bin/activate
python -m pytest tests/ -v --tb=short
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/felixwang/devspace/cc-project/cqh-agent
git add api-server/
git commit -m "feat: add integration smoke tests and test conftest"
```

---

## Self-Review Checklist

**1. Spec coverage:**
- [x] Users table → Task 2 (models), Task 3 (schemas), Task 4 (repo), Task 5 (auth service)
- [x] OrgConfigs table → Task 2, 3, 4, 8
- [x] TopicOutlines table → Task 2, 3, 4, 9
- [x] Articles table → Task 2, 3, 4, 10
- [x] JWT auth (login, me) → Task 5
- [x] Dashboard API → Task 7
- [x] Discovery API (config, list, refresh) → Task 8
- [x] Outlines API (CRUD + generate + regenerate) → Task 9
- [x] Workbench API (CRUD + AI suggest/metrics) → Task 10
- [x] AI Service (Qwen) → Task 6
- [x] Docker + Compose → Task 11
- [x] Frontend client update → Task 12

**2. Placeholder scan:** No TBD/TODO found. All code is complete.

**3. Type consistency:**
- UUID fields consistently use `str(uuid)` in schemas and `UUID(str_id)` in services
- All repository methods return ModelType or Optional[ModelType]
- Service methods return dict, formatted for schema validation
- AIService methods return list[dict] or dict consistently
