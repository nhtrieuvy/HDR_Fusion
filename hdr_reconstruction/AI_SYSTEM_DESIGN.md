# AI System Design: RAW HDR Reconstruction

This document is the engineering contract for future AI or human changes to this project. It records the intended data model, pipeline flow, algorithm logic, quality assumptions, performance constraints, and guardrails. Do not change these decisions casually.

## Mission

The system reconstructs HDR radiance maps from multiple camera RAW frames of the same static scene captured at different exposure times.

Primary output:

- `hdr.hdr`: float32 RGB radiance map in linear display RGB space.

Secondary output:

- `preview.png`: 8-bit RGB tone-mapped preview for visual inspection only.

Never treat `preview.png` as HDR data.

## Core Invariants

- RAW support is decoder-based, not extension-based. A file is considered RAW only if `rawpy`/LibRaw can open it.
- Exposure times are in seconds.
- Exposure override JSON takes priority over EXIF/RAW metadata.
- A scene failure must not crash the whole batch.
- An algorithm failure must not prevent other algorithms from running unless config explicitly disables continuation.
- `.hdr` data must remain linear radiance. Do not gamma-correct or tone-map it.
- Tone mapping is allowed only for PNG preview generation.
- The default comparison set is:
  - `linear_rgb_merge`
  - `weighted_linear_rgb_merge`
  - `noise_aware_weighted_linear_hdr_merge`
  - `raw_domain_weighted_hdr_merge`

## Data Representations

Each `RawFrame` stores multiple representations of the same frame:

- `raw_mosaic`: black-level corrected and white-level normalized RAW sensor data. It can be a 2D Bayer mosaic or packed multi-plane data such as `(H, W, 4)` from some DNG files.
- `cfa_pattern`: CFA or plane color description. For packed DNG data this can be like `("R", "G", "B", "G")`.
- `linear_rgb`: demosaiced, white-balanced, linear sRGB float32 from `rawpy.postprocess(... gamma=(1,1), output_color=sRGB)`.
- `rendered_ldr`: rendered 8-bit RGB preview from RAW, used only for alignment/debug previews.
- `preview_rgb`: alignment/debug proxy image.

Keep `raw_mosaic` and `linear_rgb` conceptually separate. RAW-domain algorithms merge before RGB demosaicing/color conversion. Linear RGB algorithms merge after RAW processing into linear sRGB.

## Batch Pipeline

For each scene:

1. Scan files in scene folder.
2. Validate candidate RAW files by opening with `rawpy`.
3. Read exposure time from override JSON or metadata.
4. Load RAW frames:
   - normalized RAW sensor data
   - linear sRGB float32
   - rendered preview RGB
5. Validate scene consistency:
   - at least two RAW frames
   - valid exposure times
   - exposure times sufficiently different
   - matching image size/active area
   - camera/ISO/aperture/focal length/WB warnings
6. Align using rendered preview proxy:
   - reference frame is median exposure
   - ECC warp is applied to `linear_rgb`, `raw_mosaic`, and `preview_rgb`
7. Run configured HDR algorithms.
8. Write algorithm outputs:
   - `hdr.hdr`
   - `preview.png`
   - `log.json`
9. Write scene-level:
   - `summary.json`
   - `comparison_contact_sheet.png`

## Algorithm Contracts

### Linear RGB HDR Merge

Purpose: baseline radiance estimate in linear sRGB.

Logic:

```text
radiance_i = linear_rgb_i / exposure_time_i
R = valid-pixel average(radiance_i)
```

Implementation requirement:

- Use streaming accumulation, not a full `(N,H,W,3)` radiance stack.
- Exclude very dark and near-saturated pixels using config thresholds.
- Fallback to simple exposure-normalized average when no frame is valid at a pixel.

### Weighted Linear RGB HDR Merge

Purpose: stronger linear sRGB baseline with exposure-quality weights.

Logic:

```text
w_i = triangular_weight(luminance(linear_rgb_i))
R = sum(w_i * linear_rgb_i / t_i) / sum(w_i)
```

Implementation requirement:

- Use luminance weight shared across channels.
- Use streaming accumulation.
- Fallback to simple exposure-normalized average when total weight is zero.
- Log weight statistics.

### Noise-Aware Weighted Linear HDR Merge

Purpose: recommended production-quality algorithm for current system.

Logic:

```text
exposure_quality_i = triangular_weight(luminance_i)
variance_radiance_i = (shot_noise(signal_i) + read_noise(ISO_i)^2) / t_i^2
w_i = exposure_quality_i / variance_radiance_i
R = sum(w_i * linear_rgb_i / t_i) / sum(w_i)
```

Implementation requirement:

- Use streaming accumulation.
- Use ISO-aware read noise scaling.
- Keep config values reproducible; do not silently infer camera-specific noise profiles unless they are explicitly provided.
- Log noise model parameters and weight statistics.

### RAW-domain Weighted HDR Merge

Purpose: research/advanced path that merges in sensor domain before color conversion.

Logic:

```text
raw_radiance_i = raw_mosaic_i / t_i
w_i = triangular_weight(raw_mosaic_i)
raw_HDR = sum(w_i * raw_radiance_i) / sum(w_i)
camera_rgb = demosaic_or_unpack(raw_HDR)
linear_srgb = color_correct(camera_rgb)
```

Critical color rules:

- Do not write camera RGB directly as sRGB.
- Packed RAW planes may include inactive planes. Detect and ignore inactive/zero planes before averaging repeated colors.
- Apply camera white-balance gains before color correction.
- Convert/fit RAW-domain RGB to the same linear sRGB space used by `linear_rgb`.
- Current implementation uses a reference-frame ridge fit:

```text
camera_rgb_reference -> rawpy linear_sRGB_reference
```

- Fit only on valid midtone pixels to avoid shadows, saturation, and outliers.
- Limit color-fit samples for performance.
- Log `raw_color_correction` status, matrix, ridge, sample count, and reference file.
- Repair extreme highlight chroma after RAW-domain color conversion. Bright bulbs can fall outside the midtone color fit and produce magenta/green artifacts when channels clip differently. The repair must preserve RAW-domain luminance while borrowing chroma from the best valid linear-sRGB exposure. Detect highlights using both luminance and max-channel percentiles; magenta artifacts often have low green, so luminance-only detection misses them. If the borrowed chroma is still over-saturated, limit it toward neutral luminance. Use a minimum blend for the detected highlight mask; clipped practical lights should not become magenta unless the source light is genuinely colored.
- Repair shadow chroma only when a very dark pixel is also abnormally saturated. This is a conservative cleanup for RAW-domain low-light color noise and matrix extrapolation; it must not globally desaturate shadows or change normal colored objects.

RAW-domain is allowed to differ subtly from linear RGB algorithms because the merge happens before demosaic/color processing. It must not have gross magenta/green casts. If it does, inspect inactive planes, WB gains, and color correction first.

## Tone Mapping Contract

Tone mapping is preview-only. It must never modify or replace `.hdr`.

Supported methods:

- `simple_global`: `x / (1 + x)`
- `reinhard`: extended global Reinhard with configurable white point
- `aces_filmic`: ACES-style filmic curve

Required preview flow:

1. Convert HDR to float32.
2. Record `has_nan` and `has_inf`.
3. Replace NaN/Inf safely.
4. Clamp negative values to zero.
5. Apply preview exposure.
6. Optional percentile normalization using luminance percentiles, not absolute max.
7. If `preserve_color=true`, tone-map luminance and scale RGB by `Y_mapped / Y`.
8. Optional small shadow lift.
9. Apply gamma correction, default `2.2`.
10. Convert to uint8 RGB.

Important:

- Do not normalize by global max by default.
- Do not per-channel tone-map when `preserve_color=true`.
- Do not output multiple exposure preview PNGs by default. The current output contract is one `preview.png` per algorithm.

## Performance Rules

- Avoid building full `(N,H,W,C)` stacks when a streaming sum is possible.
- Avoid storing multiple full-size copies of HDR data.
- Keep algorithm runtime separate from output write time in logs.
- `save_intermediate_preview` defaults to `false` because debug preview I/O is expensive on large batches.
- Full-size `.hdr` write is large. A 5472 x 3648 RGB float32 map is about 239 MB in memory before encoding.
- Contact sheets use previews only and should never read `.hdr`.

## Logging Rules

Each algorithm log must include:

- scene and algorithm names
- input files and exposure times
- metadata summaries
- validation warnings/errors
- alignment status
- runtime seconds
- output write seconds
- HDR min/max/mean/dynamic range
- NaN/Inf counts
- tone mapping metadata
- algorithm-specific weight/noise/color stats

Scene summary must include:

- algorithm success/fail status
- runtime and output write timing
- HDR statistics
- output paths
- scene-level warnings/errors
- preprocessing timings

## Config Rules

Use config for algorithm behavior. Do not hard-code tuning constants when they affect output quality.

Expected config groups:

- `linear_merge`
- `weighted_merge`
- `noise_aware_weighted_merge`
- `raw_domain_weighted_merge`
- `tonemapping`
- `alignment`
- `debug`

Adding a new algorithm requires:

1. Implementing the common `HDRAlgorithm` interface.
2. Registering it in `hdr/registry.py`.
3. Adding config defaults.
4. Logging algorithm-specific stats.
5. Adding it to contact sheet ordering only if it is part of the comparison set.

## Guardrails For Future AI Changes

Do not:

- Reintroduce Debevec/Robertson into the default comparison set unless explicitly requested.
- Identify RAW files by extension only.
- Gamma-correct or tone-map `.hdr`.
- Save multiple preview exposures unless the user explicitly asks.
- Treat RAW-domain camera RGB as sRGB.
- Average inactive packed RAW planes.
- Remove RAW-domain highlight chroma repair without replacing it with a calibrated highlight reconstruction strategy.
- Remove graceful scene/algorithm failure handling.
- Replace streaming merges with full stacks without a measured reason.
- Hide warnings/errors to make logs look clean.
- Track `input/`, `output/`, `__pycache__/`, or `*.pyc`.

Prefer:

- Reproducible deterministic processing.
- Explicit config knobs.
- Linear-space math for HDR.
- Luminance-based tone mapping with color preservation.
- Conservative logging over silent assumptions.
- Small, testable changes with synthetic checks and at least one real-scene sanity run when RAW data is available.

## Current Recommended Output

For production-quality output today, prefer:

```text
noise_aware_weighted_linear_hdr_merge
```

For research comparison, keep:

```text
weighted_linear_rgb_merge
raw_domain_weighted_hdr_merge
linear_rgb_merge
```

RAW-domain is valuable for future quality gains, but it is more sensitive to RAW packing, CFA interpretation, demosaic quality, white balance, and camera-to-sRGB conversion.
