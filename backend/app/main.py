from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import settings


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
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
    }


static_path = Path("static")

if static_path.exists():

    app.mount(
        "/",
        StaticFiles(
            directory=str(static_path),
            html=True,
        ),
        name="frontend",
    )