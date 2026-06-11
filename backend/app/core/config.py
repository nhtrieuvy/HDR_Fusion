from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


def load_dotenv_files() -> None:
    """Load root/backend .env files without adding a runtime dependency."""
    backend_root = Path(__file__).resolve().parents[2]
    repo_root = backend_root.parent
    for path in (repo_root / ".env", backend_root / ".env"):
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


load_dotenv_files()


class Settings(BaseModel):
    app_name: str = "HDR Fusion Backend"
    api_prefix: str = "/v1"
    environment: str = "local"

    database_url: str = "sqlite:///./.scratch/hdr_fusion.db"
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"
    celery_task_always_eager: bool = False
    broker_connection_retry_on_startup: bool = True

    storage_backend: Literal["local", "s3"] = "local"
    storage_bucket: str = "hdr-fusion"
    storage_local_root: Path = Path(".local_storage")
    s3_endpoint_url: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_region: str = "auto"
    s3_public_endpoint_url: str | None = None
    s3_public_base_url: str | None = None

    scratch_root: Path = Path(".scratch")
    direct_upload_max_bytes: int = 2_000_000_000
    max_raw_job_concurrency: int = 1
    auto_create_db: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["http://127.0.0.1:5173", "http://localhost:5173"])
    demosaic_backend: Literal["opencv_edge_aware", "external_amaze_service"] = "opencv_edge_aware"
    amaze_service_url: str | None = None
    amaze_timeout_seconds: float = 180.0
    amaze_allow_fallback: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            environment=os.getenv("HDR_ENV", os.getenv("ENVIRONMENT", "local")),
            database_url=os.getenv("DATABASE_URL", cls.model_fields["database_url"].default),
            redis_url=os.getenv("REDIS_URL", cls.model_fields["redis_url"].default),
            celery_broker_url=os.getenv(
                "CELERY_BROKER_URL",
                os.getenv("REDIS_URL", cls.model_fields["celery_broker_url"].default),
            ),
            celery_result_backend=os.getenv(
                "CELERY_RESULT_BACKEND",
                cls.model_fields["celery_result_backend"].default,
            ),
            celery_task_always_eager=_env_bool("CELERY_TASK_ALWAYS_EAGER", False),
            broker_connection_retry_on_startup=_env_bool("BROKER_CONNECTION_RETRY_ON_STARTUP", True),
            storage_backend=os.getenv("STORAGE_BACKEND", cls.model_fields["storage_backend"].default),
            storage_bucket=os.getenv("STORAGE_BUCKET", cls.model_fields["storage_bucket"].default),
            storage_local_root=Path(os.getenv("STORAGE_LOCAL_ROOT", ".local_storage")),
            s3_endpoint_url=os.getenv("S3_ENDPOINT_URL"),
            s3_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
            s3_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY"),
            s3_region=os.getenv("S3_REGION", "auto"),
            s3_public_endpoint_url=os.getenv("S3_PUBLIC_ENDPOINT_URL"),
            s3_public_base_url=os.getenv("S3_PUBLIC_BASE_URL"),
            scratch_root=Path(os.getenv("SCRATCH_ROOT", ".scratch")),
            direct_upload_max_bytes=int(os.getenv("DIRECT_UPLOAD_MAX_BYTES", "2000000000")),
            max_raw_job_concurrency=int(os.getenv("MAX_RAW_JOB_CONCURRENCY", "1")),
            auto_create_db=_env_bool("AUTO_CREATE_DB", False),
            demosaic_backend=os.getenv("DEMOSAIC_BACKEND", "opencv_edge_aware"),
            amaze_service_url=_env_optional("AMAZE_SERVICE_URL"),
            amaze_timeout_seconds=float(os.getenv("AMAZE_TIMEOUT_SECONDS", "180")),
            amaze_allow_fallback=_env_bool("AMAZE_ALLOW_FALLBACK", True),
            cors_origins=[
                item.strip()
                for item in os.getenv("CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",")
                if item.strip()
            ],
        )


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _env_optional(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


settings = Settings.from_env()
