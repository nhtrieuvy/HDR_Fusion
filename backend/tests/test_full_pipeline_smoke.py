import numpy as np

from app.core.config import settings
from app.db.session import SessionLocal, init_database
from app.pipelines.raw_hdr_fusion.pipeline import RawHDRFusionPipeline
from app.schemas.image_set import ImageSetCreate
from app.schemas.job import JobCreate
from app.schemas.project import ProjectCreate
from app.schemas.source_image import SourceImageCreate
from app.services.artifact_service import list_job_artifacts
from app.services.image_set_service import create_image_set, register_source_image
from app.services.job_service import create_job
from app.services.preset_service import load_preset
from app.services.project_service import create_project
from app.services.storage_service import StorageService


def test_full_pipeline_smoke_with_synthetic_npy(tmp_path):
    settings.storage_backend = "local"
    settings.storage_local_root = tmp_path / "storage"
    settings.scratch_root = tmp_path / "scratch"
    init_database()

    with SessionLocal() as db:
        project = create_project(db, ProjectCreate(name="smoke"))
        image_set = create_image_set(db, ImageSetCreate(project_id=project.id, name="synthetic"))
        storage = StorageService()
        base = np.ones((32, 32), dtype=np.float32) * 0.28
        base[8:12, 20:24] = 0.95
        for idx, scale in enumerate([0.35, 1.0, 2.6]):
            arr = np.clip(base * scale, 0.0, 1.0).astype(np.float32)
            local = tmp_path / f"frame_{idx}.npy"
            np.save(local, arr)
            key = f"original/local/{project.id}/{image_set.id}/frame_{idx}.npy"
            storage.put_file(local, key, "application/octet-stream")
            register_source_image(
                db,
                SourceImageCreate(
                    image_set_id=image_set.id,
                    storage_key=key,
                    original_filename=local.name,
                    mime_type="application/octet-stream",
                    file_size=local.stat().st_size,
                ),
            )
        job = create_job(db, JobCreate(image_set_id=image_set.id), load_preset("real_estate_natural"))
        report = RawHDRFusionPipeline(db).run(job.id)
        artifacts = list_job_artifacts(db, job.id)
        artifact_types = {artifact.artifact_type for artifact in artifacts}
        assert report["pipeline"]["status"] == "phase3_complete"
        assert "final_jpg" in artifact_types
        assert "final_png" in artifact_types
        assert "final_webp" in artifact_types
        assert "final_tiff" in artifact_types
        assert "thumbnail_webp" not in artifact_types
        assert "qc_report" in artifact_types
