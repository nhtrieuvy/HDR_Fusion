# AI System Design: RAW HDR Fusion Backend

This document is the active engineering contract for the current backend in `backend/app`.
It replaces the old comparison/legacy `hdr_reconstruction` contract. The production path is a
single RAW-domain HDR pipeline for interior real-estate photography.

## Mission

Produce a clean, natural, production-ready interior image from a bracketed RAW stack.

Priority order:

1. Control blown windows, lamps, and halo spill.
2. Preserve true recoverable detail from the RAW bracket.
3. Keep walls, doors, trim, and ceilings neutral.
4. Keep wood/floor/cabinets warm and visually attractive.
5. Avoid fake HDR, false color, haze, ghosting, and overprocessed sharpening.

## Active Backend Stack

- API: FastAPI in `backend/app/main.py`.
- Worker: Celery in `backend/app/workers`.
- Database: PostgreSQL.
- Broker/cache: Redis.
- Object storage: local filesystem or S3/MinIO through `StorageService`.
- RAW decode: `rawpy`/LibRaw when available; synthetic `.npy` path exists for tests.
- Image processing: NumPy + OpenCV + imageio.

## Active Pipeline

Implementation entry point:

- `backend/app/pipelines/raw_hdr_fusion/pipeline.py`

Main stages:

1. `input_audit`
   - Validate frame count and RAW readability.
2. `raw_decode_and_black_white_normalization`
   - Decode RAW without auto brightness and with linear gamma.
   - Normalize black/white levels once.
3. `reference_and_exposure_order`
   - Sort dark-to-bright.
   - Use middle exposure as reference.
   - Estimate effective exposure ratios from RAW overlap where confidence is high.
4. `alignment_proxy_ecc_audit`
   - Translation ECC on RGB proxy.
   - Warp RAW safely without breaking CFA/packed planes.
5. `typed_source_truth_masks`
   - Build typed source masks, not one global highlight mask.
   - Separate window core, recoverable window detail, unrecoverable window clipping, lamp core, bloom, floor glare, reflections, broad bright false positives.
6. `raw_domain_weighted_merge`
   - Merge RAW radiance with low/high threshold rejection.
   - Reject near-black and near-clipped pixels.
7. `valid_exposure_source_compositor`
   - Composite recoverable source/window detail from valid dark RAW exposure before AMaZE/fallback demosaic.
   - Window detail uses the darkest RAW frame when it contains real non-clipped detail.
8. `radiance_safety_before_amaze`
   - Scale/shoulder radiance before demosaic.
   - Protect source regions from technical clipping.
9. `AMaZE Demosaic`
   - Requested demosaic path is AMaZE.
   - For packed multi-plane DNG or unavailable AMaZE, fallback converts/demosaics safely and records method in metrics.
10. `candidate_finishing_and_tonemap`
    - Linear deglare/debloom.
    - Highlight chroma repair.
    - Neutral surface balance.
    - Shadow chroma protection.
    - `interior_color_grade`.
    - Interior tone mapping.
    - Sharpen final candidate.
11. `rule_based_qc`
    - Select best candidate using clipping, halo, color cast, colorfulness, unrecoverable source clipping, and source/window metrics.
12. `export_final_outputs`
    - JPG, PNG, WebP, and TIFF artifacts.

## Three Quality Layers

### Layer 1: Truth Recovery From RAW

Goal: recover only data that exists in the bracket.

Key files:

- `backend/app/cv/hdr/typed_source_masks.py`
- `backend/app/cv/hdr/valid_source_compositor.py`

Rules:

- Window recovery must be based on the darkest RAW frame containing non-clipped texture/detail.
- If the darkest frame is clipped, mark it unrecoverable. Do not claim exterior recovery.
- Broad bright walls/countertops must be rejected as source cores.
- Source masks must remain 2D spatial masks even for packed `(H, W, 4)` RAW data.

Important metrics:

- `window_core_coverage`
- `window_recoverable_detail_coverage`
- `window_unrecoverable_coverage`
- `window_exterior_detail_confidence`
- `source_compositor_coverage`
- `window_recovery_coverage`

### Layer 2: Source Reconstruction / Debloom

Goal: reduce lamp/window glare without globally darkening the room.

Key files:

- `backend/app/cv/finishing/linear_deglare.py`
- `backend/app/cv/finishing/debloom.py`
- `backend/app/cv/finishing/highlight_chroma_repair.py`

Rules:

- Treat lamp core, halo/bloom, window pane, frame edge, reflection, and floor glare differently.
- Compress halo/spill more than the source core.
- Protect fixture/window edges.
- Do this in linear space before tone mapping.

### Layer 3: Interior Color Grade

Goal: make the image more attractive after factual HDR recovery is done.

Key file:

- `backend/app/cv/finishing/interior_color_grade.py`

Rules:

- Add controlled vibrance to midtone materials.
- Add mild warmth to wood-like surfaces.
- Protect neutral walls/doors/ceilings from color pollution.
- Protect source/window/lamp masks from saturation boosts.
- Add mild clarity outside sources.
- This layer is not allowed to hallucinate exterior window detail.

## Config Contract

Config is parsed in:

- `backend/app/pipelines/raw_hdr_fusion/config.py`

Preset files:

- `backend/presets/real_estate_natural.yaml`
- `backend/presets/bright_interior.yaml`
- `backend/presets/conservative_hdr.yaml`
- `backend/presets/window_control.yaml`
- `backend/presets/artifact_safe.yaml`

Important groups:

- `hdr`: exposure thresholds, RAW merge thresholds, source/window compositor controls.
- `radiance_safety`: AMaZE/fallback input scale and source ceiling.
- `finishing`: deglare, debloom, saturation freshness, neutral/chroma/shadow controls.
- `color_grade`: vibrance, wood warmth, clarity, source protection, neutral protection.
- `export`: output quality.

Do not add hardcoded tuning constants in the pipeline when they affect image quality. Add them to `PipelineConfig` and presets.

## Production Defaults

Default preset: `real_estate_natural`.

Use `window_control` when:

- windows/lamps are still visually too hot;
- the scene has real exterior detail in darker brackets;
- QC reports high halo/source clipping.

Use `artifact_safe` when:

- alignment or color artifacts are more important than vividness.

## Quality Gate

The output is not production-ready if:

- technical clipping after processing is high;
- source halo score is high;
- neutral walls/doors/ceiling have visible color cast;
- colorfulness is too low;
- window detail is claimed but `window_exterior_detail_confidence` is near zero;
- `window_unrecoverable_coverage` or `unrecoverable_source_coverage` is significant;
- source masks bleed heavily into walls/ceilings.

If RAW data lacks exterior detail, the correct behavior is a controlled bright window, not hallucinated sky/buildings.

## Verification

Run from `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m compileall app -q
```

Docker rebuild, when Docker Desktop is running:

```powershell
docker compose -f backend/docker/docker-compose.yml up -d --build --force-recreate api worker
```
