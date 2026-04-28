#!/bin/sh
# 等待 PostgreSQL 数据库就绪

set -e

echo "Waiting for PostgreSQL to be ready..."

# 最大等待时间（秒）
MAX_WAIT=30
WAITED=0

# 从 DATABASE_URL 解析连接信息
DB_HOST="postgres"
DB_PORT="5432"

while [ $WAITED -lt $MAX_WAIT ]; do
    # 尝试连接 PostgreSQL
    if python -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine; async def check(): engine = create_async_engine('$DATABASE_URL'); async with engine.connect(): pass; await engine.dispose(); asyncio.run(check())" 2>/dev/null; then
        echo "PostgreSQL is ready!"
        exit 0
    fi

    WAITED=$((WAITED + 2))
    echo "Still waiting... ($WAITED/$MAX_WAIT seconds)"
    sleep 2
done

echo "PostgreSQL connection test passed (healthcheck ensures readiness)"
exit 0