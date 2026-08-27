# ==========================================
# Stage 1: Build React using Bun
# ==========================================

FROM oven/bun:1 AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/bun.lock* ./

RUN bun install --frozen-lockfile

COPY frontend/ .

RUN bun run build


# ==========================================
# Stage 2: Install Python dependencies using uv
# ==========================================

FROM ghcr.io/astral-sh/uv:latest AS backend-builder

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock ./

RUN uv sync \
    --frozen \
    --no-dev \
    --no-install-project


# ==========================================
# Stage 3: Lightweight Python production image
# ==========================================

FROM python:3.12-slim

WORKDIR /app


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"


# Copy Python virtual environment
COPY --from=backend-builder \
    /app/.venv \
    /app/.venv


# Copy backend
COPY backend/ .


# Copy compiled React files
COPY --from=frontend-builder \
    /frontend/dist \
    /app/static


EXPOSE 8000


CMD [
    "uvicorn",
    "app.main:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8000",
    "--workers",
    "1"
]
