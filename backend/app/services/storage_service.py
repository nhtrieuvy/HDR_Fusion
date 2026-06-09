from __future__ import annotations

import shutil
from pathlib import Path
from typing import BinaryIO

from app.core.config import settings


class StorageService:
    _checked_buckets: set[str] = set()

    def __init__(self) -> None:
        self.backend = settings.storage_backend
        settings.storage_local_root.mkdir(parents=True, exist_ok=True)

    def original_key(self, user_id: str, project_id: str, image_set_id: str, source_image_id: str, filename: str) -> str:
        ext = Path(filename).suffix.lower() or ".raw"
        return f"original/{user_id}/{project_id}/{image_set_id}/{source_image_id}{ext}"

    def local_path(self, storage_key: str) -> Path:
        clean = storage_key.replace("\\", "/").lstrip("/")
        root = settings.storage_local_root.resolve()
        path = (root / clean).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"Storage key escapes local storage root: {storage_key}")
        return path

    def presign_put(self, storage_key: str, content_type: str | None = None, expires_seconds: int = 3600) -> str:
        if self.backend == "local":
            return f"local://{self.local_path(storage_key).as_posix()}"
        self._ensure_bucket()
        client = self._s3_client()
        url = client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.storage_bucket,
                "Key": storage_key,
                **({"ContentType": content_type} if content_type else {}),
            },
            ExpiresIn=expires_seconds,
        )
        return self._rewrite_public_endpoint(url)

    def presign_get(self, storage_key: str, expires_seconds: int = 3600) -> str:
        if self.backend == "local":
            return f"local://{self.local_path(storage_key).as_posix()}"
        if settings.s3_public_base_url:
            return f"{settings.s3_public_base_url.rstrip('/')}/{storage_key}"
        client = self._s3_client()
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.storage_bucket, "Key": storage_key},
            ExpiresIn=expires_seconds,
        )
        return self._rewrite_public_endpoint(url)

    def put_file(self, source: Path, storage_key: str, content_type: str | None = None) -> None:
        if self.backend == "local":
            target = self.local_path(storage_key)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            return
        self._ensure_bucket()
        kwargs = {"ExtraArgs": {"ContentType": content_type}} if content_type else {}
        self._s3_client().upload_file(str(source), settings.storage_bucket, storage_key, **kwargs)

    def put_stream(self, stream: BinaryIO, storage_key: str, content_type: str | None = None) -> int:
        if self.backend == "local":
            target = self.local_path(storage_key)
            target.parent.mkdir(parents=True, exist_ok=True)
            total = 0
            with target.open("wb") as output:
                while chunk := stream.read(1024 * 1024):
                    total += len(chunk)
                    output.write(chunk)
            return total
        self._ensure_bucket()
        kwargs = {"ExtraArgs": {"ContentType": content_type}} if content_type else {}
        self._s3_client().upload_fileobj(stream, settings.storage_bucket, storage_key, **kwargs)
        return -1

    def download_to_path(self, storage_key: str, target: Path) -> Path:
        target.parent.mkdir(parents=True, exist_ok=True)
        if self.backend == "local":
            shutil.copy2(self.local_path(storage_key), target)
        else:
            self._s3_client().download_file(settings.storage_bucket, storage_key, str(target))
        return target

    def open_stream(self, storage_key: str):
        if self.backend == "local":
            return self.local_path(storage_key).open("rb")
        response = self._s3_client().get_object(Bucket=settings.storage_bucket, Key=storage_key)
        return response["Body"]

    def exists(self, storage_key: str) -> bool:
        if self.backend == "local":
            return self.local_path(storage_key).exists()
        try:
            self._s3_client().head_object(Bucket=settings.storage_bucket, Key=storage_key)
            return True
        except Exception:
            return False

    def _s3_client(self):
        import boto3

        return boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region,
        )

    def _ensure_bucket(self) -> None:
        if settings.storage_bucket in self._checked_buckets:
            return
        client = self._s3_client()
        try:
            client.head_bucket(Bucket=settings.storage_bucket)
        except Exception:
            client.create_bucket(Bucket=settings.storage_bucket)
        self._checked_buckets.add(settings.storage_bucket)

    def _rewrite_public_endpoint(self, url: str) -> str:
        if not settings.s3_public_endpoint_url or not settings.s3_endpoint_url:
            return url
        return url.replace(settings.s3_endpoint_url.rstrip("/"), settings.s3_public_endpoint_url.rstrip("/"), 1)
