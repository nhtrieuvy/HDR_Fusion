# HDR Reconstruction From Camera RAW Brackets

This project reconstructs HDR radiance maps from multiple camera RAW frames of the same static scene captured with different shutter speeds. It supports any RAW format that the installed `rawpy`/LibRaw decoder can open, including common formats such as DNG, CR2, CR3, NEF, ARW, RAF, ORF, RW2, PEF, and SRW when decoder support is available.

The pipeline does not classify RAW files by extension. Each candidate file is validated by attempting to open it with the RAW decoder.

## Input Structure

```text
input/
  scene_01/
    img_01.NEF
    img_02.NEF
    img_03.NEF
  scene_02/
    img_01.ARW
    img_02.ARW
    img_03.ARW
```

Each scene needs at least two valid RAW files. Three to seven frames is recommended. More than nine frames are processed with a warning.

## Exposure Override

Exposure time is read from EXIF/RAW metadata unless an override JSON is provided. Override values are in seconds and preserve the order listed in JSON.

```json
{
  "scene_01": {
    "images": [
      "img_01.NEF",
      "img_02.NEF",
      "img_03.NEF"
    ],
    "exposure_times": [
      0.001,
      0.004,
      0.016
    ]
  }
}
```

If no override exists for a scene, valid RAW files are scanned and sorted by exposure time.

## Installation

```bash
cd hdr_reconstruction
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On Linux/macOS, activate with `source .venv/bin/activate`.

## Run

PowerShell:

```powershell
python main.py `
  --input ./input `
  --output ./output `
  --config ./configs/default.yaml `
  --exposure-override ./exposure_override.json
```

Command Prompt:

```bat
python main.py ^
  --input ./input ^
  --output ./output ^
  --config ./configs/default.yaml ^
  --exposure-override ./exposure_override.json
```

The exposure override argument is optional.

For implementation rules and future-agent guardrails, see `AI_SYSTEM_DESIGN.md`.

## Output Structure

```text
output/
  scene_01/
    linear_rgb_merge/
      hdr.hdr
      preview.png
      log.json
    weighted_linear_rgb_merge/
      hdr.hdr
      preview.png
      log.json
    noise_aware_weighted_linear_hdr_merge/
      hdr.hdr
      preview.png
      log.json
    raw_domain_weighted_hdr_merge/
      hdr.hdr
      preview.png
      log.json
    summary.json
    comparison_contact_sheet.png
```

The `.hdr` files are the primary HDR radiance map outputs. The `.png` files are tone-mapped previews only and should not be treated as HDR data.

## Tone Mapping

Tone mapping is used only for PNG previews. It never changes the `.hdr` radiance map.

Supported methods:

- `simple_global`: `mapped = hdr / (1 + hdr)`
- `reinhard`: extended global Reinhard curve with configurable white point.
- `aces_filmic`: ACES-style filmic curve for natural highlight rolloff and contrast.

Before tone mapping, the preview pipeline removes NaN/Inf, clamps negative values to zero, applies `exposure`, and optionally normalizes by luminance percentiles. The default avoids max-value normalization and uses `percentile_black: 0.1` and `percentile_white: 99.7` to keep highlights controlled without flattening the image.

When `preserve_color` is enabled, the curve is applied to luminance and RGB is scaled by `Y_mapped / Y`, which keeps color more stable than per-channel tone mapping. Gamma correction is applied after tone mapping, with default gamma `2.2`.

## Algorithms

### Linear RGB HDR Merge

RAW frames are demosaiced and converted to linear RGB without gamma or tone curve. Each image is divided by its exposure time, then valid radiance estimates are averaged:

```text
R(x) = mean_i(I_i(x) / t_i)
```

Very dark and nearly saturated pixels are ignored when possible.

### Weighted Linear RGB HDR Merge

This is the stronger linear baseline. It computes radiance the same way, but weights each pixel by exposure quality. A triangular luminance weight favors mid-exposed pixels and suppresses near-black or near-saturated pixels:

```text
R(x) = sum_i(w_i(x) * I_i(x) / t_i) / sum_i(w_i(x))
```

If all weights are zero, the algorithm falls back to the unweighted linear average.

### Noise-Aware Weighted Linear HDR Merge

This algorithm also merges demosaiced linear RGB frames, but its weight combines exposure quality with a simple image noise model. Pixels get lower weight when they are close to black, close to saturation, or likely dominated by read noise:

```text
w_i(x) = exposure_quality_i(x) / variance_radiance_i(x)
R(x) = sum_i(w_i(x) * I_i(x) / t_i) / sum_i(w_i(x))
```

The default noise model estimates radiance variance from normalized signal, exposure time, and ISO-scaled read noise. It is meant as a reproducible baseline when no calibrated camera noise profile is available.

### RAW-domain Weighted HDR Merge

This algorithm merges before RGB demosaicing. Each RAW mosaic is black-level corrected, white-level normalized, converted to radiance by exposure time, and merged with a triangular per-sensel weight:

```text
R_raw(x) = sum_i(w_i(x) * raw_i(x) / t_i) / sum_i(w_i(x))
```

The merged RAW radiance mosaic is then unpacked or demosaiced, white-balanced, and color-corrected into the same linear sRGB space used by the linear RGB algorithms. This keeps the merge itself in the RAW/sensor domain, while still producing an RGB `.hdr` radiance map for output and comparison.

## Validation

For every scene, the pipeline checks:

- At least two valid RAW files.
- RAW decoder can open each selected file.
- Exposure time exists, is finite, and is greater than zero.
- Exposure times are sufficiently different.
- Image dimensions and active areas match.
- Camera model, ISO, aperture, focal length, and white balance consistency where metadata is available.

Warnings are logged for mild mismatches. Errors fail only that scene, and batch processing continues when configured.

## Alignment

The reference frame is the median exposure. The first implementation uses:

- ECC alignment on preview proxies for linear RGB data.
- The same proxy ECC warp is applied to the RAW mosaic for RAW-domain merge.

If alignment fails, the pipeline logs a warning and continues with the unaligned frame.

## Limitations

- No deghosting or moving object handling yet.
- Assumes a static scene and mostly fixed viewpoint.
- Assumes same camera, resolution, ISO, aperture, white balance, focus, and focal length inside a scene.
- RAW format support depends on the installed LibRaw/rawpy version.
- RAW-domain output uses a first-pass unpack/bilinear demosaic plus reference-frame color correction after HDR merge. A future version can replace this with a higher-quality calibrated camera color pipeline.
