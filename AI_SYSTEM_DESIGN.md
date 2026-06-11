# AI System Design: HDR Fusion

Last updated: 2026-06-09

This is the canonical context file for the whole project. Any AI or human making code changes must read this file first, then update it when the architecture, pipeline, data contract, commands, limitations, or product behavior changes.

## Maintenance Rule For AI Coding

After every meaningful code change, the AI must:

1. Re-read the affected backend/frontend source.
2. Run the relevant tests/build when possible.
3. Update this file if any behavior, file path, command, artifact, pipeline stage, config, limitation, or roadmap item changed.
4. Keep this file factual. Do not claim a stage exists unless source code actually implements it.
5. Record unresolved quality issues explicitly instead of hiding them behind optimistic wording.

Canonical file:

- `D:\Study\HDR_Fusion\AI_SYSTEM_DESIGN.md`

The older backend-local design file should only point to this root file to avoid stale context.

## Product Goal

HDR Fusion reconstructs production-ready real-estate interior photos from bracketed RAW input files.

Primary quality goals, in priority order:

1. Controlled windows, lamps, and other strong light sources.
2. Recover true exterior/window detail only when it exists in the RAW bracket.
3. Neutral walls, doors, trim, and ceilings.
4. Warm but realistic wood/floor/cabinet color.
5. Natural brightness, local contrast, and depth.
6. No fake HDR, heavy haze, purple/magenta shadows, green/yellow light halos, blur, ghosting, or overprocessed texture.

Important product rule:

- If RAW data does not contain exterior detail, the system must keep the window bright but controlled. It must not claim true recovery.
- AI-generated exterior replacement, if ever added, must be a separate explicit mode, not default HDR recovery.

## Current High-Level Architecture

```text
frontend React/Vite UI
    |
    | HTTP /v1
    v
FastAPI backend
    |
    | creates jobs / serves artifacts
    v
Celery worker
    |
    | RAW HDR pipeline
    v
PostgreSQL + Redis + S3/MinIO or local storage
```

Backend:

- API: `backend/app/main.py`
- AMaZE service app: `backend/amaze_service/main.py`
- Job pipeline: `backend/app/pipelines/raw_hdr_fusion/pipeline.py`
- Worker: `backend/app/workers`
- Presets: `backend/presets/*.yaml`
- Tests: `backend/tests`
- Docker compose: `backend/docker/docker-compose.yml`

Frontend:

- App: `frontend/src`
- Result gallery: `frontend/src/components/results`
- Artifact/download API: `frontend/src/api/artifacts.ts`
- i18n: `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/vi.json`

## Runtime Stack

Backend:

- Python
- FastAPI
- Celery
- PostgreSQL
- Redis
- S3/MinIO or local filesystem storage
- NumPy
- OpenCV
- imageio
- rawpy/LibRaw when available

Frontend:

- React
- TypeScript
- Vite
- TanStack Query
- i18next
- Tailwind-style utility classes
- lucide-react icons

## Current Backend Pipeline

Implementation:

- `backend/app/pipelines/raw_hdr_fusion/pipeline.py`

Pipeline stages:

```text
input_audit
-> raw_decode_and_black_white_normalization
-> reference_and_exposure_order
-> alignment_proxy_ecc_audit
-> typed_source_truth_masks
-> raw_domain_weighted_merge
-> valid_exposure_source_compositor
-> radiance_safety_before_amaze
-> demosaic_amaze_or_fallback
-> candidate_finishing_and_tonemap
-> rule_based_qc
-> export_final_outputs
```

### Stage Details

`input_audit`

- Validates RAW input count and readability.
- Uses configured min/max frame count.

`raw_decode_and_black_white_normalization`

- Decodes RAW through `rawpy` when available.
- Uses no auto brightness and linear gamma for RAW pipeline input.
- Normalizes black/white once through `backend/app/cv/raw/black_white.py`.
- Tracks `raw_min`, `raw_max`, `raw_median`, `raw_p95`, `raw_p99`, `black_level_used`, `white_level_used`, `raw_clip_percentage`.

`reference_and_exposure_order`

- Sorts frames dark-to-bright.
- Uses middle exposure as reference.
- Uses EXIF ratio fallback and RAW-overlap ratio estimate when confidence is sufficient.
- Code: `backend/app/cv/hdr/exposure_ratio.py`.

`alignment_proxy_ecc_audit`

- Uses RGB proxy ECC translation.
- Rejects low-confidence or large translation.
- Warps RAW safely by CFA-aware translation where accepted.
- Code: `backend/app/cv/alignment`.

`typed_source_truth_masks`

- Creates 2D source/window masks even for packed multi-plane RAW.
- Current masks include:
  - `window_core`
  - `window_recoverable_detail`
  - `window_unrecoverable`
  - `window_frame_edge`
  - `light_bulb_core`
  - `light_bloom`
  - `specular_reflection`
  - `floor_glare`
  - `wall_near_source`
  - `ceiling_near_source`
  - `countertop_or_wall_false_positive`
  - `unrecoverable_clipped_source`
  - `valid_dark_source_detail`
- Code: `backend/app/cv/hdr/typed_source_masks.py`.

`raw_domain_weighted_merge`

- Merges RAW radiance before demosaic.
- Uses smooth exposure weights.
- Rejects near-black and near-clipped pixels.
- Code: `backend/app/cv/hdr/merge_raw_domain.py`.

`valid_exposure_source_compositor`

- Composites recoverable source/window detail from valid dark RAW exposure before demosaic.
- For window detail, it uses the darkest RAW frame where the mask says detail is recoverable.
- Current blend is Gaussian-feathered, not yet full edge-aware/Laplacian blending.
- Code: `backend/app/cv/hdr/valid_source_compositor.py`.

`radiance_safety_before_amaze`

- Scales/shoulders radiance before demosaic.
- Protects source regions from technical clipping.
- Code: `backend/app/cv/hdr/radiance_safety.py`.

`demosaic_amaze_or_fallback`

- The pipeline requests AMaZE.
- The stage now has a configured backend boundary.
- Supported demosaic backends:
  - `opencv_edge_aware`: current runnable fallback.
  - `external_amaze_service`: HTTP bridge for a real AMaZE service that accepts merged Bayer mosaic arrays.
- Current implementation includes a RawTherapee-based AMaZE engine command:
  - `backend/native/amaze_engine/rawtherapee_amaze_engine.py`
  - WSL installer: `backend/native/amaze_engine/install_wsl.sh`
  - Docker image wiring: `backend/docker/Dockerfile.amaze-service`
- The RawTherapee engine path creates a temporary synthetic DNG from the merged Bayer mosaic, calls `rawtherapee-cli` with AMaZE demosaic, reads TIFF output, applies inverse sRGB transfer, and returns `linear_rgb`.
- RawTherapee can crop Bayer borders during demosaic. The engine restores output shape to the original mosaic size with edge padding and records `shape_restoration_*` metrics.
- Current limitation: this is a practical AMaZE integration, not a direct in-memory AMaZE array port. It depends on synthetic DNG metadata and RawTherapee TIFF output behavior.
- Current fallback for merged Bayer mosaic is OpenCV edge-aware demosaic when configured or when service fallback is allowed.
- Packed/multichannel DNG paths use direct multichannel RAW-to-RGB conversion.
- Code: `backend/app/cv/demosaic/amaze_adapter.py`.
- External service client: `backend/app/cv/demosaic/external_amaze_service.py`.
- External service app: `backend/amaze_service`.

AMaZE integration rule:

- AMaZE for merged synthetic Bayer mosaic must be integrated through an explicit bridge contract, not hidden inside the pipeline.
- The backend must export a standardized AMaZE input package:
  - `amaze_input.npy`: 2D merged Bayer mosaic, float32, normalized linear radiance.
  - `amaze_meta.json`: shape, dtype, CFA pattern, camera white balance, color description, white/black scale assumptions, and job id.
- The external bridge must return:
  - `linear_rgb.npy`: HxWx3 float32 linear RGB.
  - `amaze_metrics.json`: method name, bridge backend, input/output min/max/percentiles, warnings, runtime, and whether fallback was used.
- Backend validation must reject bridge output if shape, channel count, dtype, finite values, or radiance scale are invalid.
- If the bridge fails, the system may fall back to OpenCV only with explicit metrics/warnings. It must never label OpenCV fallback as real AMaZE.
- For Docker/production, prefer a separate Linux/WSL AMaZE microservice over trying to call host WSL from inside containers.
- Runtime env:
  - `DEMOSAIC_BACKEND=opencv_edge_aware|external_amaze_service`
  - `AMAZE_SERVICE_URL=http://127.0.0.1:8077`
  - `AMAZE_TIMEOUT_SECONDS=180`
  - `AMAZE_ALLOW_FALLBACK=true|false`
- AMaZE service env:
  - `AMAZE_ENGINE_COMMAND`
  - `AMAZE_ENGINE_TIMEOUT_SECONDS`
  - `AMAZE_SERVICE_MAX_REQUEST_BYTES`

AMaZE service command protocol:

```text
AMAZE_ENGINE_COMMAND input.npz output.npz
```

or with placeholders:

```text
AMAZE_ENGINE_COMMAND ... {input} ... {output}
```

The native engine must write `output.npz` containing:

- `linear_rgb`: HxWx3 float32 linear RGB.
- `metrics_json`: JSON object string.

If `AMAZE_ENGINE_COMMAND` is missing, `amaze_service` returns HTTP 503. This is intentional and prevents fake AMaZE output.

Included RawTherapee AMaZE command:

```text
python /app/native/amaze_engine/rawtherapee_amaze_engine.py {input} {output}
```

For WSL:

```text
python /mnt/d/Study/HDR_Fusion/backend/native/amaze_engine/rawtherapee_amaze_engine.py {input} {output}
```

`candidate_finishing_and_tonemap`

- Generates multiple candidates:
  - `natural`
  - `bright`
  - `conservative_hdr`
  - `window_control`
  - `artifact_safe`
- Finishing operations:
  - linear deglare
  - linear debloom
  - highlight chroma repair
  - neutral balance
  - shadow chroma protection
  - interior color grade
  - interior tone mapping
  - sharpening
- Key files:
  - `backend/app/cv/finishing/linear_deglare.py`
  - `backend/app/cv/finishing/debloom.py`
  - `backend/app/cv/finishing/highlight_chroma_repair.py`
  - `backend/app/cv/finishing/neutral_color.py`
  - `backend/app/cv/finishing/interior_color_grade.py`
  - `backend/app/cv/finishing/tone_mapping.py`
  - `backend/app/cv/finishing/interior_finish.py`

`rule_based_qc`

- Scores candidates with clipping, halo, color cast, colorfulness, sharpness, unrecoverable source clipping, and window detail confidence.
- Code: `backend/app/cv/qc/report.py`.

`export_final_outputs`

- Current final exports for new jobs:
  - `final_jpg`
  - `final_png`
  - `final_webp`
  - `final_tiff`
- `thumbnail_webp` is no longer generated for new jobs.
- Code: `backend/app/pipelines/raw_hdr_fusion/pipeline.py`.

## Current Frontend Behavior

Main result UI:

- `frontend/src/components/results/ResultGallery.tsx`
- `frontend/src/components/results/DownloadButtons.tsx`

Download behavior:

- Download buttons must download files, not open a new tab.
- Download uses blob-based helper in `frontend/src/api/artifacts.ts`.
- Result view should expose final output buttons in this order:
  1. JPG
  2. PNG
  3. WEBP
  4. TIFF
- For old jobs without `final_png`, frontend can generate PNG from `final_jpg` or `final_webp`.

Artifact content API:

- `GET /v1/artifacts/{artifact_id}` returns metadata and content URL.
- `GET /v1/artifacts/{artifact_id}/content` streams inline by default.
- `GET /v1/artifacts/{artifact_id}/content?download=true` returns attachment download.

## Presets

Preset files:

- `backend/presets/real_estate_natural.yaml`
- `backend/presets/bright_interior.yaml`
- `backend/presets/conservative_hdr.yaml`
- `backend/presets/window_control.yaml`
- `backend/presets/artifact_safe.yaml`

Default intended preset:

- `real_estate_natural`

Use `window_control` when:

- windows or lamps are still too hot;
- exterior detail exists in dark RAW frames;
- QC reports high halo/source clipping.

Use `artifact_safe` when:

- alignment/ghosting/haze/artifact risk is higher than the need for vivid color.

Config parser:

- `backend/app/pipelines/raw_hdr_fusion/config.py`

Config groups currently used:

- `input`
- `raw`
- `hdr`
- `radiance_safety`
- `finishing`
- `color_grade`
- `export`

Runtime-only demosaic environment:

- `DEMOSAIC_BACKEND`
- `AMAZE_SERVICE_URL`
- `AMAZE_TIMEOUT_SECONDS`
- `AMAZE_ALLOW_FALLBACK`
- `AMAZE_ENGINE_COMMAND`
- `AMAZE_ENGINE_TIMEOUT_SECONDS`
- `AMAZE_SERVICE_MAX_REQUEST_BYTES`

Do not add hardcoded image-quality constants directly in pipeline logic. If a parameter changes output quality, it should go into `PipelineConfig` and presets.

## Current Known Quality Limitations

These are active limitations as of 2026-06-09.

1. Real AMaZE is wired through RawTherapee CLI, but not yet quality-validated on real scenes.
   - The code now has an external AMaZE service client, service app, Docker wiring, validation contract, and RawTherapee AMaZE command engine.
   - The implementation uses synthetic DNG + RawTherapee CLI rather than direct in-memory AMaZE.
   - Without an AMaZE service, the default local mode falls back to OpenCV edge-aware demosaic for merged Bayer mosaic.
   - This can limit color/detail quality.
   - Required next step is empirical image validation against real bracket scenes, especially checking that RawTherapee output transfer/color behavior does not conflict with downstream color/tone stages.

2. RAW color science is still incomplete.
   - Current path applies camera white balance.
   - It does not yet implement a robust camera profile / color matrix / fitted RAW-to-sRGB transform for every case.
   - This can affect wall neutrality, color richness, and material rendering.

3. Window recovery is still heuristic.
   - It relies on bright connected components plus detail statistics in darkest RAW luma.
   - It does not yet use semantic window segmentation.
   - It does not yet use full edge-aware or Laplacian blending.

4. Deglare/debloom is simple.
   - It uses blurred source masks and luma-dependent attenuation.
   - It does not yet model lamp core, halo, spill, reflection, and window pane with separate physical behavior.

5. Tone mapping is source-aware but still mostly global.
   - It uses metering and p99 guard.
   - It does not yet have separate local tone curves for interior, window, lamp core, lamp halo, and reflections.

6. AI model is not implemented.
   - There is no trained model.
   - There is no inference stage.
   - There is no dataset capture/training pipeline yet.

## Current Technical Conclusion: Core Before AI

If color, lighting, and window detail are still below target, the next engineering priority is still HDR core, not AI replacement.

Reasons:

- True exterior/window recovery must come from RAW bracket data, not AI hallucination.
- Current source/window compositor is not yet strong enough.
- Current demosaic/color path has known deterministic limitations.
- Current tone/deglare/debloom stages are still heuristic.

AI should be added later as a controlled finishing layer, not as a substitute for RAW truth recovery.

Correct future order:

```text
RAW bracket
-> deterministic HDR core
-> source/window truth recovery
-> deglare/debloom
-> demosaic/color/tone mapping
-> optional learned finishing
-> QC guardrail
-> export
```

## Recommended Next Core Work

Priority 1: AMaZE / demosaic and color science

- Validate and tune the RawTherapee AMaZE engine path, then decide whether a direct in-memory AMaZE port is still needed.
- Bridge implementation order:
  1. Done: add config/env plumbing and a `DemosaicBackend` boundary around `demosaic_amaze_or_fallback`.
  2. Done: add an AMaZE HTTP service client and tests for success/fail-fast/fallback.
  3. Done: add the AMaZE HTTP service shell, Docker service, command protocol, health endpoint, and contract checker.
  4. Done: add RawTherapee-based AMaZE command engine and Docker/WSL install path.
  5. Next: run integration checks with Docker/WSL RawTherapee installed.
  6. Next: compare OpenCV fallback vs RawTherapee AMaZE on real scenes before tuning later color/window stages.
- Add stronger camera color conversion:
  - use metadata color matrix where possible;
  - fit RAW-domain RGB to reference rawpy linear sRGB when feasible;
  - log color transform metrics.

Priority 2: Window/source recovery

- Improve `typed_source_masks.py`:
  - better window pane/frame detection;
  - distinguish lamp, window, reflection, floor glare, and bright wall more reliably;
  - report per-region recoverability.
- Improve `valid_source_compositor.py`:
  - replace simple Gaussian blend with edge-aware/Laplacian blending;
  - preserve window frame edges;
  - avoid washing detail back out during demosaic/tone map.

Priority 3: Source-aware tone mapping

- Add separate highlight handling for:
  - window core;
  - window halo/frame;
  - lamp core;
  - lamp halo;
  - specular reflection;
  - normal bright neutral walls.
- Keep interior exposure independent from source compression.

Priority 4: Better deterministic interior color

- Improve neutral-surface detection.
- Improve wood/material color mapping.
- Add stronger but bounded vibrance/local contrast controls.
- Preserve neutral walls/ceilings.

## Future AI / Learned Finishing Plan

AI model and training are related but different:

- AI model: trained inference artifact such as ONNX/PT/safetensors.
- Training: process used to create the model from data.

Recommended AI role:

- learned finishing;
- local relighting;
- clean wall/ceiling;
- pleasing color style;
- shadow naturalness;
- mild haze/artifact reduction.

AI should not claim true exterior detail recovery unless the mode explicitly allows generated exterior replacement.

Future AI architecture:

```text
deterministic final RGB
+ linear RGB
+ source/window/neutral/shadow/highlight masks
+ QC metrics
-> learned_finishing_model
-> guarded blend
-> QC
-> fallback to deterministic output if fail
```

Recommended model output:

- adjustment maps, not unconstrained final image:
  - exposure_delta
  - color_delta
  - saturation_delta
  - contrast_delta
  - shadow_lift_map
  - highlight_compression_map

Potential future folders:

```text
backend/app/ml/
  inference/
    model_registry.py
    onnx_runner.py
    learned_finishing.py
  preprocessing/
    feature_pack.py
  postprocessing/
    guarded_blend.py
  training/
    dataset.py
    train.py
    losses.py
    export_onnx.py
```

Dataset plan:

1. Add dataset capture from real jobs:
   - deterministic final;
   - RAW bracket references;
   - source/window/neutral/shadow masks;
   - candidates;
   - QC metrics;
   - selected output.
2. Collect manual retouch targets for hard interior scenes.
3. Pretrain only if useful using public datasets, then fine-tune on own interior data.
4. Deploy model only with QC and fallback.

## Debug / Metrics That Matter

For window/source issues:

- `window_core_coverage`
- `window_recoverable_detail_coverage`
- `window_unrecoverable_coverage`
- `window_exterior_detail_confidence`
- `window_recovery_coverage`
- `window_recovery_mean_amount`
- `unrecoverable_source_coverage`
- `amaze_input_technical_clip_percentage`
- `final_p99_luminance`
- `highlight_clip_percentage`
- `near_clip_percentage`
- `halo_score`

For color issues:

- `neutral_surface_coverage`
- `neutral_surface_rgb_mean`
- `estimated_color_cast`
- `neutral_gains`
- `color_cast`
- `colorfulness`
- `interior_color_grade_vibrance_coverage`
- `interior_color_grade_wood_coverage`

For demosaic/color correctness:

- `demosaic_method`
- `requested_demosaic_method`
- `amaze_fallback_reason`
- `camera_white_balance_applied`
- `camera_white_balance_gains`
- `linear_rgb_min`
- `linear_rgb_max`
- `linear_rgb_median`
- `linear_rgb_p95`
- `linear_rgb_p99`

## Commands

Run backend tests:

```powershell
cd D:\Study\HDR_Fusion\backend
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m compileall app -q
```

Run frontend build:

```powershell
cd D:\Study\HDR_Fusion\frontend
npm run build
```

Run backend/frontend locally:

```powershell
cd D:\Study\HDR_Fusion\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
cd D:\Study\HDR_Fusion\frontend
npm run dev
```

Run Docker backend services from project root:

```powershell
cd D:\Study\HDR_Fusion
docker compose -f backend/docker/docker-compose.yml up -d --build --force-recreate
```

If already inside `D:\Study\HDR_Fusion\backend`, use:

```powershell
docker compose -f docker/docker-compose.yml up -d --build --force-recreate
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/v1/health
```

## Recent Decisions

2026-06-09:

- Root `AI_SYSTEM_DESIGN.md` is now the canonical context file.
- HDR quality issues should continue to be addressed in deterministic core before adding an AI model.
- AI model is planned only as future learned finishing with guarded blend and QC fallback.
- Final output artifacts for new jobs are JPG, PNG, WebP, and TIFF.
- Frontend download buttons should download files directly and must not open a new tab.
