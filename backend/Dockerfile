# ─── Stage 1: Build Frontend ───
FROM node:22-alpine AS frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ─── Stage 2: Python Backend + Frontend Static ───
FROM python:3.12-slim
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend code
COPY backend/app/ ./app/
COPY backend/alembic.ini .
COPY backend/alembic/ ./alembic/
COPY backend/entrypoint.sh .
RUN chmod +x entrypoint.sh

# Frontend build output
COPY --from=frontend /frontend/dist/ ./static/

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
