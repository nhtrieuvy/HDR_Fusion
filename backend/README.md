# HDR Fusion Backend

Production-oriented Python backend for RAW bracket HDR reconstruction for interior / real-estate photography.

## Layout

```text
app/                 FastAPI, DB, workers, pipeline, CV modules
presets/             Production preset YAML snapshots
docker/              Local API/worker/Postgres/Redis/MinIO stack
tests/               Regression tests
hdr_reconstruction/  Legacy CLI reference code
MEF/                 Legacy MEF reference utilities
```

## Local API Without Docker

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend automatically loads environment variables from the repository root `.env` and then `backend/.env` if present. Values in the shell still take precedence.

Health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/v1/health
```

## Demosaic / AMaZE Mode

The backend now has an explicit demosaic backend boundary.

Default local mode:

```env
DEMOSAIC_BACKEND=opencv_edge_aware
AMAZE_ALLOW_FALLBACK=true
```

This keeps jobs runnable with the current OpenCV edge-aware fallback. The job metrics will report:

```text
demosaic_method=opencv_edge_aware_fallback
amaze_fallback_used=true
```

Real AMaZE service mode:

```env
DEMOSAIC_BACKEND=external_amaze_service
AMAZE_SERVICE_URL=http://127.0.0.1:8077
AMAZE_TIMEOUT_SECONDS=180
AMAZE_ALLOW_FALLBACK=false
```

In this mode the worker sends the merged Bayer mosaic to:

```text
POST {AMAZE_SERVICE_URL}/v1/demosaic/amaze
content-type: application/vnd.hdr-fusion.amaze+npz
```

Request `.npz` fields:

- `mosaic`: 2D float32 merged Bayer mosaic after radiance safety.
- `meta_json`: JSON string with CFA pattern, camera white balance, color description, shape, and contract version.

Response `.npz` fields:

- `linear_rgb`: HxWx3 float32 linear RGB.
- `metrics_json`: JSON object string with AMaZE runtime/method diagnostics.

With `AMAZE_ALLOW_FALLBACK=false`, a missing or invalid AMaZE service fails the job deliberately. This is the recommended quality-control setting when validating real AMaZE integration because it prevents OpenCV fallback from being mistaken for AMaZE.

With `AMAZE_ALLOW_FALLBACK=true`, service failures fall back to OpenCV edge-aware demosaic and record the fallback reason in job metrics.

Run the AMaZE service separately:

```powershell
cd D:\Study\HDR_Fusion\backend
.\.venv\Scripts\Activate.ps1
uvicorn amaze_service.main:app --host 127.0.0.1 --port 8077
```

Check the service:

```powershell
Invoke-RestMethod http://127.0.0.1:8077/v1/health
python scripts/check_amaze_service.py --url http://127.0.0.1:8077
```

The AMaZE service requires `AMAZE_ENGINE_COMMAND` to point to a real AMaZE engine that accepts `input.npz output.npz`. If this variable is empty, the service returns HTTP 503 by design.

This repo includes a RawTherapee-based AMaZE engine command:

```text
native/amaze_engine/rawtherapee_amaze_engine.py
```

It creates a temporary synthetic DNG from the merged Bayer mosaic, calls `rawtherapee-cli` with AMaZE demosaic, reads TIFF output, and returns the `.npz` contract.

Recommended WSL setup:

```bash
cd /mnt/d/Study/HDR_Fusion/backend
chmod +x native/amaze_engine/install_wsl.sh
native/amaze_engine/install_wsl.sh
source .venv-amaze-service/bin/activate
export AMAZE_ENGINE_COMMAND="python /mnt/d/Study/HDR_Fusion/backend/native/amaze_engine/rawtherapee_amaze_engine.py {input} {output}"
uvicorn amaze_service.main:app --host 0.0.0.0 --port 8077
```

Recommended production layout:

```text
backend worker -> HTTP -> amaze_service -> native AMaZE engine
```

Do not run host WSL commands directly from inside the main API/worker container. Run `amaze_service` in the WSL/Linux environment that owns the native AMaZE engine, then call it over HTTP.

## Docker Stack

```powershell
cd backend
docker compose -f docker/docker-compose.yml up --build
```

Services:

- API: `http://127.0.0.1:8000`
- AMaZE service: `http://127.0.0.1:8077`
- MinIO console: `http://127.0.0.1:9001`
- Flower: `http://127.0.0.1:5555`

Docker Compose sets `S3_PUBLIC_ENDPOINT_URL=http://127.0.0.1:9000`, so artifact URLs returned by the API are browser-accessible even though API/worker talk to MinIO internally through `http://minio:9000`.

For Docker AMaZE strict mode, set root `.env`:

```env
DEMOSAIC_BACKEND=external_amaze_service
AMAZE_ALLOW_FALLBACK=false
```

Then run:

```powershell
cd D:\Study\HDR_Fusion\backend
docker compose -f docker/docker-compose.yml up -d --build --force-recreate api worker amaze-service
```

## Pipeline

The worker runs:

1. input audit
2. RAW decode and black/white normalization
3. exposure order and RAW-overlap exposure ratio
4. proxy ECC alignment with CFA-safe RAW warp
5. typed source truth masks
6. RAW-domain weighted HDR merge
7. valid dark-source compositor
8. radiance safety before AMaZE input
9. demosaic adapter through configured backend: OpenCV fallback or external AMaZE service
10. linear deglare/debloom, chroma repair, neutral balance
11. interior-aware tone mapping candidates
12. rule-based QC and final export

The system distinguishes true capture clipping from technical processing clipping and does not hallucinate exterior/window detail.
