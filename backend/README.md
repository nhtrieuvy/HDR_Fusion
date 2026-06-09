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

## Docker Stack

```powershell
cd backend
docker compose -f docker/docker-compose.yml up --build
```

Services:

- API: `http://127.0.0.1:8000`
- MinIO console: `http://127.0.0.1:9001`
- Flower: `http://127.0.0.1:5555`

Docker Compose sets `S3_PUBLIC_ENDPOINT_URL=http://127.0.0.1:9000`, so artifact URLs returned by the API are browser-accessible even though API/worker talk to MinIO internally through `http://minio:9000`.

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
9. demosaic adapter with explicit fallback reporting
10. linear deglare/debloom, chroma repair, neutral balance
11. interior-aware tone mapping candidates
12. rule-based QC and final export

The system distinguishes true capture clipping from technical processing clipping and does not hallucinate exterior/window detail.
