FROM python:3.12-slim-bookworm

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY alembic.ini .

# 运行数据库迁移并启动服务
CMD ["sh", "-c", "alembic upgrade head && python -m app.main"]