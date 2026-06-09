# HDR Fusion

This repository is split into two top-level folders:

```text
backend/
frontend/
```

## Backend

`backend/` contains the recreated Python production backend plus the restored legacy reference code.

```text
backend/app/
backend/presets/
backend/docker/
backend/tests/
backend/hdr_reconstruction/
backend/MEF/
```

See [backend/README.md](backend/README.md).

## Frontend

`frontend/` contains the React/TypeScript dashboard.

Run it with:

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## Frontend Environment

Local development uses the root `.env` file for both backend and frontend. The frontend Vite config reads environment variables from the repository root.

For an API available at `http://127.0.0.1:8000`:

```env
VITE_API_BASE_URL=/v1
VITE_UPLOAD_MODE=direct
VITE_ENABLE_DEBUG_ARTIFACTS=true
VITE_POLL_INTERVAL_MS=2000
VITE_ENABLE_MOCK_API=false
```

For frontend-only development without a backend:

```env
VITE_ENABLE_MOCK_API=true
```
