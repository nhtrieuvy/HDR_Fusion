# Backend Refactor Plan

## Current Inventory

- `backend/hdr_reconstruction/`: legacy CLI RAW bracket HDR pipeline.
- `backend/MEF/`: older multi-exposure fusion utilities.
- `backend/app/`: recreated production-oriented Python backend.
- `backend/presets/`: production preset snapshots.
- `backend/docker/`: local API/worker/Postgres/Redis/MinIO stack.
- `backend/tests/`: regression tests for backend and computational photography primitives.

## Safe To Keep

- RAW metadata/decode ideas from `hdr_reconstruction/io` and `preprocessing/raw_processor.py`.
- RAW-domain weighted merge principle from `hdr_reconstruction/hdr/raw_domain_weighted_hdr_merge.py`.
- Tone-mapping safety ideas from `hdr_reconstruction/tonemapping/tonemap.py`.
- MEF code only as optional reference baseline, not the production RAW HDR path.

## Replace Or Avoid

- CLI batch orchestration as production interface.
- Broad source/highlight masks that capture walls, ceiling, doors, or countertops.
- Display-space global glare reduction.
- Any logic that claims exterior/window recovery when darkest RAW is clipped.
- Direct image processing in API request handlers.

## Regression Tests Needed

- RAW decode no auto-bright/gamma.
- Black/white normalization keeps clip statistics.
- Exposure sort and ratio ignore clipped pixels.
- Typed source masks reject broad bright wall/ceiling regions.
- RAW merge rejects saturated highlight pixels.
- Source compositor uses valid darkest source detail and reports unrecoverable clipping.
- Radiance safety reports AMaZE input technical clipping.
- Tone mapping avoids high final clipping.
- QC catches halo, color cast, and mask leakage.

## CLI To Backend Migration

1. Store source RAW files in object storage.
2. Register metadata in `source_images`.
3. Create `jobs` with preset config snapshot.
4. Celery worker downloads source objects into per-job scratch.
5. Worker writes every step metric into `job_steps`.
6. Worker uploads originals/debug/masks/candidates/final outputs to object storage.
7. Worker registers artifacts in PostgreSQL.
8. API remains metadata/control plane only.

