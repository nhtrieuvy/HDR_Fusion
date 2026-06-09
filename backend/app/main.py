from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import artifacts, health, image_sets, jobs, projects, uploads
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import init_database

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_db:
        init_database()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(uploads.router, prefix=settings.api_prefix)
app.include_router(projects.router, prefix=settings.api_prefix)
app.include_router(image_sets.router, prefix=settings.api_prefix)
app.include_router(jobs.router, prefix=settings.api_prefix)
app.include_router(artifacts.router, prefix=settings.api_prefix)

