from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, Response

from amaze_service.contract import AmazeContractError, decode_request_npz, encode_response_npz
from amaze_service.engine import AmazeEngineError, run_external_amaze_engine
from amaze_service.settings import settings


app = FastAPI(title="HDR Fusion AMaZE Service")


@app.get("/v1/health")
def health() -> dict[str, object]:
    return {
        "status": "ok" if settings.engine_command else "not_configured",
        "service": "external_amaze_service",
        "engine_configured": settings.engine_command is not None,
        "engine_timeout_seconds": settings.engine_timeout_seconds,
    }


@app.post("/v1/demosaic/amaze")
async def demosaic_amaze(request: Request) -> Response:
    content = await request.body()
    if len(content) > settings.max_request_bytes:
        raise HTTPException(status_code=413, detail="AMaZE request payload is too large")
    try:
        amaze_request = decode_request_npz(content)
        amaze_response = run_external_amaze_engine(
            amaze_request,
            engine_command=settings.engine_command,
            timeout_seconds=settings.engine_timeout_seconds,
        )
        payload = encode_response_npz(amaze_response)
    except AmazeContractError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AmazeEngineError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return Response(content=payload, media_type="application/vnd.hdr-fusion.amaze+npz")
