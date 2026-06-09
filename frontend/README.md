# HDR Fusion Frontend

React + TypeScript dashboard for the Python HDR Fusion backend.

## Local Development

Start the backend from `../backend` or configure another compatible HDR Fusion API.

Local backend:

```powershell
cd ..\backend
uvicorn app.main:app --reload
```

Install and run the frontend:

```powershell
npm install
npm run dev
```

Open the Vite URL, normally:

```text
http://127.0.0.1:5173
```

## Environment

Default local setup uses the root `.env` file and Vite proxy:

```env
VITE_API_BASE_URL=/v1
VITE_UPLOAD_MODE=direct
VITE_ENABLE_DEBUG_ARTIFACTS=true
VITE_POLL_INTERVAL_MS=2000
```

Use `direct` upload for a backend that accepts multipart uploads through `/v1/uploads/direct`. Use `presigned` only when the storage endpoint is browser-accessible and CORS is configured.

Mock mode for frontend-only UI work:

```env
VITE_ENABLE_MOCK_API=true
```

## Backend Notes

The expected backend has project list/create, image set create, source image register, job create/detail/steps/results, retry, re-enhance, and artifact access endpoints.

If the backend does not expose list-all-jobs or list-image-sets-by-project endpoints, the frontend keeps image sets and recent jobs created from the UI in local browser storage for dashboard/project convenience.
