#!/bin/bash
set -e

echo "Running database migrations..."

# Check if tables already exist (e.g., created via Supabase SQL Editor)
# If so, stamp the migration as complete instead of re-creating
TABLE_EXISTS=$(python3 -c "
from app.config import settings
from sqlalchemy import create_engine, text
e = create_engine(settings.DATABASE_URL)
with e.connect() as c:
    result = c.execute(text(\"SELECT to_regclass('public.users')\"))
    row = result.fetchone()
    print(row[0] if row[0] else 'NOT_FOUND')
    c.commit()
" 2>/dev/null || echo 'ERROR')

if [ "$TABLE_EXISTS" = "ERROR" ]; then
    echo "Could not check table existence, attempting migration..."
    alembic upgrade head
elif [ "$TABLE_EXISTS" != "NOT_FOUND" ]; then
    echo "Tables already exist (users = $TABLE_EXISTS), stamping migration as applied..."
    alembic stamp head
else
    echo "Tables not found, running full migration..."
    alembic upgrade head
fi

echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
