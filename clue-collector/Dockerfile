FROM python:3.12-slim-bookworm

WORKDIR /app

# 安装系统依赖（Playwright需要）
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    # Playwright浏览器依赖
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装Playwright Chromium浏览器
RUN playwright install chromium --with-deps

# 复制应用代码
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY alembic.ini .

# 运行数据库迁移并启动服务
CMD ["sh", "-c", "alembic upgrade head && python -m app.main"]