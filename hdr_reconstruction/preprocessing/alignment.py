from __future__ import annotations

import cv2
import numpy as np

from hdr_reconstruction.hdr.base import SceneData
from hdr_reconstruction.utils.image_utils import bgr_to_rgb, rgb_to_bgr, to_gray_uint8


def reference_index(exposure_times: np.ndarray) -> int:
    if exposure_times.size == 0:
        return 0
    return int(np.argsort(exposure_times)[len(exposure_times) // 2])


def align_scene(scene_data: SceneData, config: dict) -> SceneData:
    alignment_config = config.get("alignment", {})
    if not alignment_config.get("enabled", True):
        scene_data.alignment_info = {"enabled": False, "status": "skipped"}
        return scene_data

    ref_idx = reference_index(scene_data.exposure_times)
    warnings: list[str] = []
    linear_status = _align_linear_ecc(scene_data, ref_idx, warnings)
    if config.get("raw", {}).get("create_rendered_ldr_for_classical_hdr", False):
        classical_status = _align_classical_mtb(scene_data, warnings)
    else:
        classical_status = "skipped"
    scene_data.alignment_info = {
        "enabled": True,
        "reference_index": ref_idx,
        "reference_file": scene_data.frames[ref_idx].metadata.filename,
        "method_linear": alignment_config.get("method_linear", "ecc_or_feature"),
        "method_raw_domain": alignment_config.get("method_raw_domain", "proxy_ecc_warped_mosaic"),
        "method_classical": alignment_config.get("method_classical", "align_mtb"),
        "linear_status": linear_status,
        "raw_domain_status": linear_status,
        "classical_status": classical_status,
        "warnings": warnings,
    }
    scene_data.warnings.extend(warnings)
    return scene_data


def _align_linear_ecc(scene_data: SceneData, ref_idx: int, warnings: list[str]) -> str:
    ref_gray = to_gray_uint8(scene_data.frames[ref_idx].preview_rgb).astype(np.float32) / 255.0
    h, w = ref_gray.shape
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 80, 1e-5)
    ok_count = 0

    for idx, frame in enumerate(scene_data.frames):
        if idx == ref_idx:
            ok_count += 1
            continue
        gray = to_gray_uint8(frame.preview_rgb).astype(np.float32) / 255.0
        warp = np.eye(2, 3, dtype=np.float32)
        try:
            cv2.findTransformECC(ref_gray, gray, warp, cv2.MOTION_EUCLIDEAN, criteria, None, 5)
            frame.linear_rgb = cv2.warpAffine(
                frame.linear_rgb,
                warp,
                (w, h),
                flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
                borderMode=cv2.BORDER_REFLECT,
            )
            frame.raw_mosaic = cv2.warpAffine(
                frame.raw_mosaic,
                warp,
                (w, h),
                flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
                borderMode=cv2.BORDER_REFLECT,
            )
            frame.preview_rgb = cv2.warpAffine(
                frame.preview_rgb,
                warp,
                (w, h),
                flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP,
                borderMode=cv2.BORDER_REFLECT,
            )
            ok_count += 1
        except Exception as exc:
            warnings.append(f"WARNING: ECC linear alignment failed for {frame.metadata.filename}: {exc}")
    return "success" if ok_count == len(scene_data.frames) else "partial"


def _align_classical_mtb(scene_data: SceneData, warnings: list[str]) -> str:
    images_bgr = [rgb_to_bgr(frame.rendered_ldr) for frame in scene_data.frames]
    try:
        align = cv2.createAlignMTB()
        aligned: list[np.ndarray] = []
        align.process(images_bgr, aligned)
        if len(aligned) != len(scene_data.frames):
            warnings.append("WARNING: AlignMTB returned unexpected number of frames")
            return "skipped"
        for frame, bgr in zip(scene_data.frames, aligned):
            frame.rendered_ldr = bgr_to_rgb(bgr)
        return "success"
    except Exception as exc:
        warnings.append(f"WARNING: AlignMTB failed: {exc}")
        return "failed_unaligned_used"
