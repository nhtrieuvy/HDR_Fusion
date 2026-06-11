# RawTherapee AMaZE Engine

This is the concrete AMaZE engine command used by `amaze_service`.

Command:

```text
python native/amaze_engine/rawtherapee_amaze_engine.py input.npz output.npz
```

It:

1. Reads HDR Fusion `input.npz`.
2. Converts the merged Bayer mosaic to a temporary synthetic DNG.
3. Calls `rawtherapee-cli` with AMaZE demosaic.
4. Reads RawTherapee TIFF output.
5. Restores output shape to the original mosaic size if RawTherapee crops border pixels.
6. Converts the sRGB TIFF values back to approximate linear RGB.
7. Writes HDR Fusion `output.npz`.

## WSL Install

Run inside Ubuntu WSL:

```bash
cd /mnt/d/Study/HDR_Fusion/backend
chmod +x native/amaze_engine/install_wsl.sh
native/amaze_engine/install_wsl.sh
```

Start the service:

```bash
cd /mnt/d/Study/HDR_Fusion/backend
source .venv-amaze-service/bin/activate
export AMAZE_ENGINE_COMMAND="python /mnt/d/Study/HDR_Fusion/backend/native/amaze_engine/rawtherapee_amaze_engine.py {input} {output}"
uvicorn amaze_service.main:app --host 0.0.0.0 --port 8077
```

Check from Windows PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8077/v1/health
cd D:\Study\HDR_Fusion\backend
.\.venv\Scripts\python.exe scripts\check_amaze_service.py --url http://127.0.0.1:8077
```

## Docker

The `amaze-service` Docker image installs RawTherapee and PiDNG and sets:

```env
AMAZE_ENGINE_COMMAND=python /app/native/amaze_engine/rawtherapee_amaze_engine.py {input} {output}
```

The Dockerfile installs `build-essential` because PiDNG builds a small C extension during `pip install`.

Build/run:

```powershell
cd D:\Study\HDR_Fusion\backend
docker compose -f docker/docker-compose.yml up -d --build --force-recreate amaze-service
```

Full strict HDR stack:

```env
DEMOSAIC_BACKEND=external_amaze_service
AMAZE_ALLOW_FALLBACK=false
```

```powershell
cd D:\Study\HDR_Fusion\backend
docker compose -f docker/docker-compose.yml up -d --build --force-recreate api worker amaze-service
```

## Quality Caveat

This is real RawTherapee AMaZE demosaic, but it is not a direct in-memory AMaZE port. It uses a synthetic DNG and RawTherapee TIFF output. Real scene validation is required before tuning later color/tone stages around this path.
