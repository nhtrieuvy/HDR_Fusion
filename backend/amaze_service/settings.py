from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AmazeServiceSettings:
    engine_command: str | None
    engine_timeout_seconds: float
    max_request_bytes: int

    @classmethod
    def from_env(cls) -> "AmazeServiceSettings":
        command = os.getenv("AMAZE_ENGINE_COMMAND", "").strip()
        return cls(
            engine_command=command or None,
            engine_timeout_seconds=float(os.getenv("AMAZE_ENGINE_TIMEOUT_SECONDS", "180")),
            max_request_bytes=int(os.getenv("AMAZE_SERVICE_MAX_REQUEST_BYTES", "1073741824")),
        )


settings = AmazeServiceSettings.from_env()
