from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware,
)
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
    ],
    allow_headers=[
        "Content-Type",
        "Authorization",
    ],
)


app.include_router(router)


@app.get(
    "/health",
    tags=["health"],
)
async def health_check():

    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": (
            settings.environment
        ),
    }


static_path = Path(__file__).resolve().parent.parent / (
    "static"
)

if static_path.exists():

    app.mount(
        "/",
        StaticFiles(
            directory=str(static_path),
            html=True,
        ),
        name="frontend",
    )
