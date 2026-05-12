FROM python:3.12-slim-bookworm

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock .
RUN uv sync --no-dev --frozen

COPY app/ ./app/
COPY migrations/ ./migrations/
COPY scripts/ ./scripts/
COPY alembic.ini .

CMD ["sh", "-c", "uv run alembic upgrade head && uv run python scripts/init_db.py && uv run uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT:-8001}"]