# HDR Fusion External AMaZE Service

This service is the production boundary for real AMaZE demosaic of a merged Bayer mosaic.

It does not implement AMaZE in Python. It validates the HDR Fusion `.npz` contract and calls a configured native AMaZE engine command.

## Contract

Endpoint:

```text
POST /v1/demosaic/amaze
content-type: application/vnd.hdr-fusion.amaze+npz
```

Request `.npz` fields:

- `mosaic`: 2D float32 merged Bayer mosaic after HDR merge and radiance safety.
- `meta_json`: JSON string with CFA pattern and capture metadata.

Response `.npz` fields:

- `linear_rgb`: HxWx3 float32 linear RGB.
- `metrics_json`: JSON object string with engine/runtime diagnostics.

## Engine Command

The service calls:

```text
AMAZE_ENGINE_COMMAND input.npz output.npz
```

or, if placeholders are present:

```text
AMAZE_ENGINE_COMMAND with {input} and {output}
```

Example:

```powershell
$env:AMAZE_ENGINE_COMMAND="python /path/to/real_amaze_engine.py {input} {output}"
```

The configured engine must write `output.npz` with `linear_rgb` and optional `metrics_json`.

The repository includes a RawTherapee-based AMaZE engine command:

```text
backend/native/amaze_engine/rawtherapee_amaze_engine.py
```

It creates a temporary synthetic DNG from the merged Bayer mosaic, calls `rawtherapee-cli` with AMaZE demosaic, reads the TIFF output, and writes the expected `.npz`.

## Local Run

From `D:\Study\HDR_Fusion\backend`:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn amaze_service.main:app --host 127.0.0.1 --port 8077
```

Health:

```powershell
Invoke-RestMethod http://127.0.0.1:8077/v1/health
```

Contract check:

```powershell
python scripts/check_amaze_service.py --url http://127.0.0.1:8077
```

If `AMAZE_ENGINE_COMMAND` is empty, health returns `not_configured` and demosaic requests return HTTP 503. This is intentional; the service must not fake AMaZE.

## Recommended WSL Layout

Run this service inside WSL/Linux where RawTherapee can run:

```bash
cd /mnt/d/Study/HDR_Fusion/backend
chmod +x native/amaze_engine/install_wsl.sh
native/amaze_engine/install_wsl.sh
source .venv-amaze-service/bin/activate
export AMAZE_ENGINE_COMMAND="python /mnt/d/Study/HDR_Fusion/backend/native/amaze_engine/rawtherapee_amaze_engine.py {input} {output}"
uvicorn amaze_service.main:app --host 0.0.0.0 --port 8077
```

Then backend on Windows can use:

```env
DEMOSAIC_BACKEND=external_amaze_service
AMAZE_SERVICE_URL=http://127.0.0.1:8077
AMAZE_ALLOW_FALLBACK=false
```

Docker worker should use:

```env
AMAZE_SERVICE_URL=http://host.docker.internal:8077
```

or the compose-provided internal service:

```env
AMAZE_SERVICE_URL=http://amaze-service:8077
```

## Docker AMaZE Service

`docker/Dockerfile.amaze-service` installs RawTherapee and PiDNG and wires:

```env
AMAZE_ENGINE_COMMAND=python /app/native/amaze_engine/rawtherapee_amaze_engine.py {input} {output}
```

Build/run:

```powershell
cd D:\Study\HDR_Fusion\backend
docker compose -f docker/docker-compose.yml up -d --build --force-recreate amaze-service
```

Check:

```powershell
Invoke-RestMethod http://127.0.0.1:8077/v1/health
.\.venv\Scripts\python.exe scripts\check_amaze_service.py --url http://127.0.0.1:8077
```
