from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np

from amaze_service.contract import AmazeContractError, AmazeRequest, AmazeResponse, validate_response


class AmazeEngineError(RuntimeError):
    pass


def run_external_amaze_engine(
    request: AmazeRequest,
    *,
    engine_command: str | None,
    timeout_seconds: float,
) -> AmazeResponse:
    if not engine_command:
        raise AmazeEngineError("AMAZE_ENGINE_COMMAND is not configured")

    with tempfile.TemporaryDirectory(prefix="hdr-amaze-") as temp_dir_raw:
        temp_dir = Path(temp_dir_raw)
        input_path = temp_dir / "amaze_input.npz"
        output_path = temp_dir / "amaze_output.npz"
        _write_engine_input(input_path, request)
        command = _build_command(engine_command, input_path, output_path)
        started = time.perf_counter()
        completed = subprocess.run(
            command,
            cwd=temp_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        runtime = time.perf_counter() - started
        if completed.returncode != 0:
            stderr = completed.stderr.strip()[-4000:]
            raise AmazeEngineError(f"AMaZE engine failed with exit code {completed.returncode}: {stderr}")
        if not output_path.exists():
            raise AmazeEngineError("AMaZE engine did not create amaze_output.npz")
        response = _read_engine_output(output_path)
        response.metrics.update(
            {
                "amaze_engine_runtime_seconds": float(runtime),
                "amaze_engine_stdout_tail": completed.stdout.strip()[-1000:],
                "amaze_engine_command_configured": True,
            }
        )
        return response


def _write_engine_input(path: Path, request: AmazeRequest) -> None:
    np.savez_compressed(
        path,
        mosaic=request.mosaic.astype(np.float32, copy=False),
        meta_json=np.asarray(json.dumps(request.meta), dtype=np.str_),
    )


def _read_engine_output(path: Path) -> AmazeResponse:
    try:
        with np.load(path, allow_pickle=False) as data:
            if "linear_rgb" not in data:
                raise AmazeContractError("engine output missing linear_rgb")
            rgb = data["linear_rgb"].astype(np.float32)
            metrics: dict[str, Any] = {}
            if "metrics_json" in data:
                metrics_raw = str(data["metrics_json"].item())
                parsed = json.loads(metrics_raw)
                if isinstance(parsed, dict):
                    metrics.update(parsed)
    except AmazeContractError:
        raise
    except Exception as exc:
        raise AmazeEngineError(f"AMaZE engine output is invalid: {exc}") from exc
    validate_response(rgb)
    metrics.update(
        {
            "amaze_service_engine_protocol": "npz_file_command_v1",
            "amaze_service_engine_output_path": str(path.name),
        }
    )
    return AmazeResponse(linear_rgb=rgb, metrics=metrics)


def _build_command(command_template: str, input_path: Path, output_path: Path) -> list[str]:
    if "{input}" in command_template or "{output}" in command_template:
        rendered = command_template.format(input=str(input_path), output=str(output_path))
        return _clean_command_tokens(shlex.split(rendered, posix=os.name != "nt"))
    command = _clean_command_tokens(shlex.split(command_template, posix=os.name != "nt"))
    return [*command, str(input_path), str(output_path)]


def _clean_command_tokens(tokens: list[str]) -> list[str]:
    return [token.strip().strip('"').strip("'") for token in tokens]
