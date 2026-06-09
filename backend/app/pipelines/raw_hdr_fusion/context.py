from __future__ import annotations

from dataclasses import dataclass

from app.db.models import Job
from app.pipelines.raw_hdr_fusion.config import PipelineConfig


@dataclass
class PipelineContext:
    job: Job
    config: PipelineConfig

