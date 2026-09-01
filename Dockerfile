# ============================================
# Stage 1: Build React frontend using Bun (Native arm64)
# ============================================
FROM oven/bun:1 AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json ./
COPY frontend/bun.lock* ./

RUN --mount=type=cache,target=/root/.bun/install/cache \
    bun install --frozen-lockfile

COPY frontend/ .

RUN bun run build


# ============================================
# Stage 2: Build Python environment using uv
# ============================================
FROM python:3.12-slim-bookworm AS backend-builder

WORKDIR /app

# Installs native arm64 uv binary directly from PyPI (no apt/ghcr needed)
RUN pip install --no-cache-dir uv

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY backend/pyproject.toml ./
COPY backend/uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync \
    --frozen \
    --no-dev \
    --no-install-project


# ============================================
# Stage 3: Production runtime
# ============================================
FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

COPY --from=backend-builder \
    /app/.venv \
    /app/.venv

COPY backend/ /app/

COPY --from=frontend-builder \
    /frontend/dist \
    /app/static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
