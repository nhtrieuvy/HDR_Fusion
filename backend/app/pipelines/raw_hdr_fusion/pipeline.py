from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import imageio.v2 as imageio
import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.cv.alignment.ecc import estimate_translation_ecc
from app.cv.alignment.proxy import rgb_proxy_to_gray
from app.cv.alignment.raw_warp import warp_raw_mosaic_safely
from app.cv.audit.bracket_audit import audit_raw_files
from app.cv.audit.exposure_sort import FrameExposure, relative_exposure_ratios, sort_dark_to_bright
from app.cv.demosaic.amaze_adapter import demosaic_amaze_or_fallback
from app.cv.finishing.debloom import apply_linear_debloom
from app.cv.finishing.export import write_jpeg, write_png, write_tiff_float, write_webp
from app.cv.finishing.highlight_chroma_repair import repair_highlight_chroma
from app.cv.finishing.interior_finish import CandidateConfig, candidate_configs
from app.cv.finishing.interior_color_grade import apply_interior_color_grade
from app.cv.finishing.linear_deglare import apply_linear_deglare
from app.cv.finishing.neutral_color import apply_neutral_balance
from app.cv.finishing.shadow_chroma_protection import protect_shadow_chroma
from app.cv.finishing.sharpen import sharpen_uint8
from app.cv.finishing.tone_mapping import tone_map_interior
from app.cv.hdr.exposure_ratio import estimate_exposure_ratios_from_raw_overlap
from app.cv.hdr.merge_raw_domain import merge_raw_domain_weighted_with_debug
from app.cv.hdr.radiance_safety import analyze_amaze_input_scale, prepare_amaze_input_with_safety
from app.cv.hdr.typed_source_masks import TypedSourceMaskResult, analyze_typed_source_masks
from app.cv.hdr.valid_source_compositor import composite_valid_sources
from app.cv.qc.report import build_rule_based_qc_report, score_candidate, select_best_candidate
from app.cv.raw.decode import DecodedRawFrame, decode_raw_frame
from app.cv.raw.shape import raw_luminance, raw_luminance_stack
from app.db.models import Job, SourceImage
from app.pipelines.raw_hdr_fusion.config import PipelineConfig, config_from_snapshot
from app.pipelines.raw_hdr_fusion.context import PipelineContext
from app.pipelines.raw_hdr_fusion.steps import PROGRESS
from app.schemas.artifact import ArtifactCreate
from app.services.artifact_service import create_artifact
from app.services.image_set_service import list_source_images
from app.services.job_service import (
    complete_step,
    fail_step,
    get_job,
    mark_job_completed,
    mark_job_failed,
    mark_job_running,
    start_step,
    update_job_progress,
)
from app.services.storage_service import StorageService


class RawHDRFusionPipeline:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.storage = StorageService()

    def run(self, job_id: str) -> dict[str, Any]:
        job = self._require_job(job_id)
        mark_job_running(self.db, job)
        try:
            audit_report = self.run_input_audit(job_id)
            pipeline_report = self.run_raw_hdr_fusion(job_id)
            report = {
                "job_id": job_id,
                "pipeline_phase": "recreated_backend_phase1_to_phase5",
                "input_audit": audit_report,
                "pipeline": pipeline_report,
            }
            metrics_artifact = self._write_json_artifact(job, "debug_metrics", f"debug/{job_id}/metrics.json", report)
            final_artifact_id = pipeline_report.get("phase3", {}).get("artifacts", {}).get("export", {}).get("final_jpg")
            qc_status = pipeline_report.get("phase3", {}).get("qc", {}).get("status", "manual_review")
            final_status = "completed" if qc_status == "pass" else "manual_review"
            mark_job_completed(self.db, job, output_artifact_id=final_artifact_id or metrics_artifact.id, status=final_status)
            return report
        except Exception as exc:
            mark_job_failed(self.db, job, str(exc))
            raise

    def run_input_audit(self, job_id: str) -> dict[str, Any]:
        job = self._require_job(job_id)
        context = self._context(job)
        step = start_step(self.db, job.id, "input_audit", PROGRESS["job_initialized"])
        try:
            sources, paths = self._prepare_local_sources(context)
            audit = audit_raw_files(paths, context.config.input_min_frames, context.config.input_max_frames)
            self._update_source_metadata(sources, audit.metadata, {})
            metrics = {**audit.metrics, "audit_status": audit.status, "source_image_count": len(sources)}
            complete_step(self.db, step, metrics=metrics, warnings=[*audit.warnings, *audit.errors])
            update_job_progress(self.db, job, PROGRESS["input_audit_complete"])
            return {"status": audit.status, "metrics": metrics, "warnings": audit.warnings, "errors": audit.errors}
        except Exception as exc:
            fail_step(self.db, step, str(exc))
            raise

    def run_raw_hdr_fusion(self, job_id: str) -> dict[str, Any]:
        job = self._require_job(job_id)
        context = self._context(job)
        sources, paths = self._prepare_local_sources(context)

        decode_step = start_step(self.db, job.id, "raw_decode_and_black_white_normalization", 12.0)
        decoded: list[DecodedRawFrame] = []
        warnings: list[str] = []
        for path in paths:
            try:
                decoded.append(decode_raw_frame(path))
            except Exception as exc:
                warnings.append(f"{path.name}: decode failed: {exc}")
        if not decoded:
            fail_step(self.db, decode_step, "No RAW frames decoded", {"warnings": warnings})
            raise RuntimeError("No RAW frames decoded")
        decode_metrics = {
            "decoded_frame_count": len(decoded),
            "raw_decode_no_auto_bright": context.config.raw_decode_no_auto_bright,
            "raw_decode_gamma": list(context.config.raw_decode_gamma),
            "frames": [
                {
                    "filename": frame.metadata.filename,
                    "raw_clip_percentage": frame.stats.get("raw_clip_percentage"),
                    "white_level_used": frame.stats.get("white_level_used"),
                    "black_level_used": frame.stats.get("black_level_used"),
                    "raw_median": frame.stats.get("raw_median"),
                    "raw_p99": frame.stats.get("raw_p99"),
                    "raw_shape": list(frame.raw_mosaic.shape),
                    "raw_ndim": int(frame.raw_mosaic.ndim),
                    "cfa_pattern": list(frame.cfa_pattern),
                    "raw_channel_labels": list(frame.raw_channel_labels or []),
                    "color_desc": frame.metadata.color_desc,
                    "camera_wb": frame.metadata.camera_wb,
                }
                for frame in decoded
            ],
        }
        complete_step(self.db, decode_step, metrics=decode_metrics, warnings=warnings)
        update_job_progress(self.db, job, PROGRESS["raw_decode_complete"])

        order_step = start_step(self.db, job.id, "reference_and_exposure_order", 22.0)
        exposures = [
            FrameExposure(
                index=i,
                exposure_time=frame.metadata.exposure_time,
                iso=frame.metadata.iso,
                aperture=frame.metadata.aperture,
                exposure_bias=frame.metadata.exposure_bias,
                measured_luminance=float(np.median(raw_luminance(frame.raw_mosaic))),
            )
            for i, frame in enumerate(decoded)
        ]
        order = sort_dark_to_bright(exposures)
        reference_index = order[len(order) // 2]
        exif_ratios = relative_exposure_ratios(exposures, reference_index)
        ratio_values = np.asarray([exif_ratios.get(i, 1.0) for i in range(len(decoded))], dtype=np.float32)
        ratio_metrics: dict[str, Any] = {"exif_relative_exposure_ratios": {str(k): v for k, v in exif_ratios.items()}}
        if all(frame.raw_mosaic.shape == decoded[0].raw_mosaic.shape for frame in decoded):
            stack_for_ratio = np.stack([frame.raw_mosaic for frame in decoded], axis=0)
            luma_stack_for_ratio = raw_luminance_stack(stack_for_ratio)
            ratio_estimate = estimate_exposure_ratios_from_raw_overlap(
                luma_stack_for_ratio,
                reference_index,
                low_threshold=context.config.exposure_ratio_low_threshold,
                high_threshold=context.config.exposure_ratio_high_threshold,
            )
            ratio_values = np.where(ratio_estimate.confidence >= 0.25, ratio_estimate.ratios, ratio_values)
            ratio_metrics.update(
                {
                    "raw_overlap_exposure_ratios": [float(v) for v in ratio_estimate.ratios],
                    "raw_overlap_confidence": [float(v) for v in ratio_estimate.confidence],
                    "raw_overlap_valid_pixel_counts": [int(v) for v in ratio_estimate.valid_pixel_counts],
                    "raw_overlap_warnings": ratio_estimate.warnings,
                    "effective_exposure_ratios": [float(v) for v in ratio_values],
                    "amaze_input_safety_reference": analyze_amaze_input_scale(
                        raw_luminance(stack_for_ratio[reference_index]),
                        input_percentile=context.config.amaze_input_percentile,
                        target_white=context.config.amaze_input_white,
                    ).metrics,
                }
            )
        order_metrics = {"exposure_order": order, "reference_index": reference_index, **ratio_metrics}
        self._update_source_metadata(sources, [frame.metadata for frame in decoded], {"order": order, "ratios": ratio_values.tolist(), "reference_index": reference_index})
        complete_step(self.db, order_step, metrics=order_metrics)
        update_job_progress(self.db, job, PROGRESS["reference_and_exposure_order_complete"])

        alignment_step = start_step(self.db, job.id, "alignment_proxy_ecc_audit", 32.0)
        alignment_metrics = self._alignment_audit(decoded, reference_index)
        complete_step(self.db, alignment_step, metrics=alignment_metrics, warnings=alignment_metrics.get("warnings", []))
        update_job_progress(self.db, job, PROGRESS["alignment_complete"])

        if not all(frame.raw_mosaic.shape == decoded[0].raw_mosaic.shape for frame in decoded):
            phase3_report = {"status": "skipped_incompatible_shapes", "warnings": ["RAW shapes do not match"]}
        else:
            stack = np.stack([frame.raw_mosaic for frame in decoded], axis=0)
            phase3_report = self._run_phase3_core(
                context,
                job,
                stack,
                order,
                reference_index,
                ratio_values,
                paths[reference_index],
                decoded[reference_index].cfa_pattern,
                decoded[reference_index].raw_channel_labels,
                decoded[reference_index].metadata.camera_wb,
                decoded[reference_index].metadata.color_desc,
            )

        report = {
            "status": "phase3_complete" if phase3_report.get("status") == "phase3_complete" else "phase3_partial",
            "decode": decode_metrics,
            "exposure": order_metrics,
            "alignment": alignment_metrics,
            "phase3": phase3_report,
        }
        self._write_json_artifact(job, "phase3_report", f"debug/{job.id}/phase3_report.json", report)
        return report

    def _run_phase3_core(
        self,
        context: PipelineContext,
        job: Job,
        stack: np.ndarray,
        exposure_order: list[int],
        reference_index: int,
        exposure_ratios: np.ndarray,
        reference_raw_path: Path | None,
        cfa_pattern: tuple[str, str, str, str] | None,
        raw_channel_labels: tuple[str, ...] | None,
        camera_wb: list[float] | None,
        color_desc: str | None,
    ) -> dict[str, Any]:
        source_step = start_step(self.db, job.id, "typed_source_truth_masks", 42.0)
        source_masks = analyze_typed_source_masks(
            stack,
            exposure_order,
            reference_index,
            {
                "source_mask_strictness": context.config.source_mask_strictness,
                "window_detail_min_std": context.config.window_detail_min_std,
                "window_detail_min_fraction": context.config.window_detail_min_fraction,
            },
        )
        mask_artifacts = self._write_mask_artifacts(job, source_masks)
        complete_step(self.db, source_step, metrics=source_masks.metrics, warnings=source_masks.warnings, artifacts=mask_artifacts)
        update_job_progress(self.db, job, PROGRESS["source_truth_complete"])

        merge_step = start_step(self.db, job.id, "raw_domain_weighted_merge", 52.0)
        merge = merge_raw_domain_weighted_with_debug(
            stack,
            exposure_ratios,
            {"low_threshold": context.config.raw_merge_low_threshold, "high_threshold": context.config.raw_merge_high_threshold},
        )
        merge_artifacts = {
            "raw_radiance_npy": self._write_npy_artifact(job, "hdr_base_raw_radiance", f"working/{job.id}/hdr_base/raw_radiance.npy", merge.radiance).id,
            "merge_weight_dark_frame": self._write_array_png_artifact(job, "merge_weight_map", f"working/{job.id}/masks/merge_weight_dark_frame.png", merge.weights[int(exposure_order[0])]).id,
            "clipped_rejection_mask": self._write_mask_artifact(job, "clipped_rejection_mask", f"working/{job.id}/masks/clipped_rejection_mask.png", merge.clipped_rejection_mask).id,
            "underexposed_rejection_mask": self._write_mask_artifact(job, "underexposed_rejection_mask", f"working/{job.id}/masks/underexposed_rejection_mask.png", merge.underexposed_rejection_mask).id,
        }
        complete_step(self.db, merge_step, metrics=merge.metrics, artifacts=merge_artifacts)
        update_job_progress(self.db, job, PROGRESS["raw_merge_complete"])

        compositor_step = start_step(self.db, job.id, "valid_exposure_source_compositor", 62.0)
        composite = composite_valid_sources(
            merge.radiance,
            merge.radiance_stack,
            source_masks,
            {
                "source_compositor_strength": context.config.source_compositor_strength,
                "source_feather_sigma": context.config.source_feather_sigma,
                "window_compositor_strength": context.config.window_compositor_strength,
                "window_feather_sigma": context.config.window_feather_sigma,
            },
            dark_index=int(exposure_order[0]),
        )
        composite_artifacts = {
            "source_composited_radiance_npy": self._write_npy_artifact(job, "hdr_base_source_composited", f"working/{job.id}/hdr_base/source_composited_radiance.npy", composite.radiance).id,
            "source_compositor_amount": self._write_array_png_artifact(job, "source_compositor_amount", f"working/{job.id}/masks/source_compositor_amount.png", composite.amount).id,
        }
        complete_step(self.db, compositor_step, metrics=composite.metrics, warnings=composite.warnings, artifacts=composite_artifacts)
        update_job_progress(self.db, job, PROGRESS["source_compositor_complete"])

        safety_step = start_step(self.db, job.id, "radiance_safety_before_amaze", 72.0)
        safety = prepare_amaze_input_with_safety(
            composite.radiance,
            source_masks,
            input_percentile=context.config.amaze_input_percentile,
            target_white=context.config.amaze_input_white,
            shoulder_strength=context.config.amaze_input_shoulder_strength,
            source_ceiling_ratio=context.config.amaze_source_ceiling_ratio,
        )
        safety_artifacts = {
            "amaze_input_npy": self._write_npy_artifact(job, "amaze_input_radiance", f"working/{job.id}/hdr_base/amaze_input.npy", safety.amaze_input).id,
            "technical_clip_mask": self._write_mask_artifact(job, "amaze_input_technical_clip_mask", f"working/{job.id}/masks/amaze_input_technical_clip_mask.png", safety.technical_clip_mask).id,
            "near_clip_mask": self._write_mask_artifact(job, "amaze_input_near_clip_mask", f"working/{job.id}/masks/amaze_input_near_clip_mask.png", safety.near_clip_mask).id,
        }
        demosaic = demosaic_amaze_or_fallback(
            safety.amaze_input,
            reference_raw_path,
            cfa_pattern,
            raw_channel_labels=raw_channel_labels,
            camera_wb=camera_wb,
            color_desc=color_desc,
            demosaic_backend=settings.demosaic_backend,
            amaze_service_url=settings.amaze_service_url,
            amaze_timeout_seconds=settings.amaze_timeout_seconds,
            amaze_allow_fallback=settings.amaze_allow_fallback,
        )
        complete_step(self.db, safety_step, metrics={**safety.metrics, **demosaic.metrics}, artifacts=safety_artifacts)
        update_job_progress(self.db, job, PROGRESS["amaze_complete"])

        finish_step = start_step(self.db, job.id, "candidate_finishing_and_tonemap", 80.0)
        candidate_outputs: dict[str, np.ndarray] = {}
        candidate_reports: list[dict[str, Any]] = []
        candidate_artifacts: dict[str, str] = {}
        selected_debug: dict[str, np.ndarray] = {}
        selected_metrics: dict[str, Any] = {}
        base_metrics = {**source_masks.metrics, **merge.metrics, **composite.metrics, **safety.metrics, **demosaic.metrics}
        candidates = candidate_configs(
            deglare_strength=context.config.finishing_deglare_strength,
            debloom_strength=context.config.finishing_debloom_strength,
            saturation_freshness=context.config.finishing_saturation_freshness,
            shadow_lift=context.config.finishing_shadow_lift,
            sharpening=context.config.finishing_sharpening,
            final_p99_target=context.config.finishing_final_p99_target,
        )
        for candidate in candidates:
            image, metrics, debug = self._finish_candidate(demosaic.rgb, source_masks, candidate, context.config)
            candidate_outputs[candidate.name] = image
            candidate_artifacts[candidate.name] = self._write_rgb_image_artifact(
                job,
                f"candidate_{candidate.name}",
                f"working/{job.id}/candidates/{candidate.name}.jpg",
                image,
                "image/jpeg",
                lambda path, img=image: write_jpeg(img, path, context.config.jpeg_quality),
            ).id
            report = score_candidate(candidate.name, image, {**base_metrics, **metrics}, source_masks.source_and_bloom)
            report["artifact_id"] = candidate_artifacts[candidate.name]
            candidate_reports.append(report)
            if candidate.name == "natural":
                selected_debug = debug
                selected_metrics = metrics

        qc_report = select_best_candidate(candidate_reports)
        selected_name = str(qc_report["selected_candidate"])
        selected_image = candidate_outputs[selected_name]
        for candidate in candidates:
            if candidate.name == selected_name:
                _, selected_metrics, selected_debug = self._finish_candidate(demosaic.rgb, source_masks, candidate, context.config)
                break
        finish_artifacts = {
            "candidates": candidate_artifacts,
            "selected_deglare_amount": self._write_array_png_artifact(job, "selected_deglare_amount", f"working/{job.id}/masks/selected_deglare_amount.png", selected_debug["deglare_amount"]).id,
            "selected_debloom_amount": self._write_array_png_artifact(job, "selected_debloom_amount", f"working/{job.id}/masks/selected_debloom_amount.png", selected_debug["debloom_amount"]).id,
            "selected_highlight_chroma_mask": self._write_mask_artifact(job, "selected_highlight_chroma_mask", f"working/{job.id}/masks/selected_highlight_chroma_mask.png", selected_debug["highlight_chroma_mask"]).id,
            "selected_shadow_chroma_amount": self._write_array_png_artifact(job, "selected_shadow_chroma_amount", f"working/{job.id}/masks/selected_shadow_chroma_amount.png", selected_debug["shadow_chroma_amount"]).id,
            "selected_color_vibrance_amount": self._write_array_png_artifact(job, "selected_color_vibrance_amount", f"working/{job.id}/masks/selected_color_vibrance_amount.png", selected_debug["color_vibrance_amount"]).id,
            "selected_color_wood_mask": self._write_mask_artifact(job, "selected_color_wood_mask", f"working/{job.id}/masks/selected_color_wood_mask.png", selected_debug["color_wood_mask"]).id,
            "selected_color_source_protection": self._write_array_png_artifact(job, "selected_color_source_protection", f"working/{job.id}/masks/selected_color_source_protection.png", selected_debug["color_source_protection"]).id,
            "selected_color_neutral_protection": self._write_array_png_artifact(job, "selected_color_neutral_protection", f"working/{job.id}/masks/selected_color_neutral_protection.png", selected_debug["color_neutral_protection"]).id,
            "neutral_surface_mask": self._write_mask_artifact(job, "neutral_surface_mask", f"working/{job.id}/masks/neutral_surface_mask.png", selected_debug["neutral_mask"]).id,
            "metering_mask": self._write_mask_artifact(job, "metering_mask", f"working/{job.id}/masks/metering_mask.png", selected_debug["metering_mask"]).id,
            "tonemap_before_auto_exposure": self._write_array_png_artifact(job, "tonemap_before_auto_exposure", f"working/{job.id}/preview/tonemap_before_auto_exposure.png", selected_debug["tonemap_before_auto_exposure"]).id,
        }
        complete_step(self.db, finish_step, metrics={**demosaic.metrics, **selected_metrics, "selected_candidate": selected_name}, artifacts=finish_artifacts)
        update_job_progress(self.db, job, PROGRESS["finishing_complete"])

        combined_metrics = {**base_metrics, **selected_metrics}
        qc_step = start_step(self.db, job.id, "rule_based_qc", 88.0)
        summary_qc = build_rule_based_qc_report(combined_metrics)
        qc_report = {**summary_qc, **qc_report, "metrics": {**combined_metrics, **qc_report.get("metrics", {})}}
        qc_artifact = self._write_json_artifact(job, "qc_report", f"debug/{job.id}/qc_report.json", qc_report)
        complete_step(self.db, qc_step, metrics=qc_report, warnings=qc_report.get("warnings", []), artifacts={"qc_report": qc_artifact.id})
        update_job_progress(self.db, job, PROGRESS["qc_complete"])

        export_step = start_step(self.db, job.id, "export_final_outputs", 94.0)
        export_artifacts = self._write_final_outputs(job, selected_image, demosaic.rgb, context)
        complete_step(self.db, export_step, metrics={"export_status": "applied"}, artifacts=export_artifacts)
        update_job_progress(self.db, job, PROGRESS["export_complete"])

        return {
            "status": "phase3_complete",
            "source_truth": source_masks.metrics,
            "raw_merge": merge.metrics,
            "source_compositor": composite.metrics,
            "radiance_safety": safety.metrics,
            "finishing": selected_metrics,
            "qc": qc_report,
            "warnings": [*source_masks.warnings, *composite.warnings],
            "artifacts": {
                "masks": mask_artifacts,
                "merge": merge_artifacts,
                "source_compositor": composite_artifacts,
                "radiance_safety": safety_artifacts,
                "finishing": finish_artifacts,
                "qc_report": qc_artifact.id,
                "export": export_artifacts,
            },
        }

    def _finish_candidate(
        self,
        linear_rgb: np.ndarray,
        source_masks: TypedSourceMaskResult,
        candidate: CandidateConfig,
        config: PipelineConfig,
    ) -> tuple[np.ndarray, dict[str, Any], dict[str, np.ndarray]]:
        deglare = apply_linear_deglare(linear_rgb, source_masks.source_and_bloom, candidate.deglare_strength)
        debloom = apply_linear_debloom(deglare.image, source_masks.source_and_bloom, candidate.debloom_strength)
        chroma = repair_highlight_chroma(
            debloom.image,
            strength=config.highlight_chroma_strength,
            source_mask=source_masks.source_and_bloom,
            source_strength=config.highlight_source_chroma_strength,
        )
        neutral = apply_neutral_balance(
            chroma.image,
            exclude_mask=source_masks.source_and_bloom,
            strength=config.neutral_balance_strength,
            max_gain=config.neutral_balance_max_gain,
        )
        shadow = protect_shadow_chroma(neutral.image, strength=config.shadow_chroma_strength)
        color = apply_interior_color_grade(
            shadow.image,
            source_mask=source_masks.source_and_bloom,
            neutral_mask=neutral.mask,
            vibrance_strength=config.color_vibrance_strength,
            wood_warmth_strength=config.color_wood_warmth_strength,
            clarity_strength=config.color_clarity_strength,
            source_protection_strength=config.color_source_protection,
            neutral_protection_strength=config.color_neutral_protection,
        )
        tone = tone_map_interior(
            color.image,
            source_mask=source_masks.source_and_bloom,
            exposure=candidate.exposure,
            shadow_lift=candidate.shadow_lift,
            saturation=candidate.saturation,
            final_p99_target=candidate.final_p99_target,
        )
        image = sharpen_uint8(tone.image, candidate.sharpen_amount)
        metrics = {
            **deglare.metrics,
            **debloom.metrics,
            **chroma.metrics,
            **neutral.metrics,
            **shadow.metrics,
            **color.metrics,
            **tone.metrics,
            "candidate_name": candidate.name,
        }
        debug = {
            "deglare_amount": deglare.amount,
            "debloom_amount": debloom.amount,
            "highlight_chroma_mask": chroma.mask.astype(np.float32),
            "neutral_mask": neutral.mask.astype(np.float32),
            "shadow_chroma_amount": shadow.amount,
            "color_vibrance_amount": color.vibrance_amount,
            "color_wood_mask": color.wood_mask.astype(np.float32),
            "color_source_protection": color.source_protection,
            "color_neutral_protection": color.neutral_protection,
            **tone.debug,
        }
        return image, metrics, debug

    def _alignment_audit(self, decoded: list[DecodedRawFrame], reference_index: int) -> dict[str, Any]:
        ref_gray = rgb_proxy_to_gray(decoded[reference_index].linear_proxy_rgb)
        details: list[dict[str, Any]] = []
        warnings: list[str] = []
        for idx, frame in enumerate(decoded):
            if idx == reference_index:
                details.append({"index": idx, "filename": frame.metadata.filename, "status": "reference", "ecc_score": 1.0})
                continue
            gray = rgb_proxy_to_gray(frame.linear_proxy_rgb)
            score, warp = estimate_translation_ecc(ref_gray, gray)
            dx = float(warp[0, 2])
            dy = float(warp[1, 2])
            translation = float(np.hypot(dx, dy))
            status = "aligned"
            if score < 0.75 or translation > 24:
                status = "rejected_identity_used"
                warnings.append(f"{frame.metadata.filename}: alignment rejected score={score:.4f} translation={translation:.2f}")
            else:
                frame.raw_mosaic = warp_raw_mosaic_safely(frame.raw_mosaic, warp, frame.cfa_pattern)
                frame.linear_proxy_rgb = cv2.warpAffine(frame.linear_proxy_rgb, warp, (ref_gray.shape[1], ref_gray.shape[0]))
            details.append({"index": idx, "filename": frame.metadata.filename, "status": status, "ecc_score": score, "dx": dx, "dy": dy, "translation_pixels": translation})
        scores = [float(item.get("ecc_score", 0.0)) for item in details]
        return {"alignment_method": "proxy_ecc_translation_safe_cfa", "alignment_confidence_mean": float(np.mean(scores)), "details": details, "warnings": warnings}

    def _prepare_local_sources(self, context: PipelineContext) -> tuple[list[SourceImage], list[Path]]:
        sources = list_source_images(self.db, context.job.image_set_id)
        if not sources:
            raise RuntimeError("Image set has no registered source images")
        local_paths: list[Path] = []
        for source in sources:
            target = settings.scratch_root / context.job.id / "originals" / source.original_filename
            self.storage.download_to_path(source.storage_key, target)
            local_paths.append(target)
        return sources, local_paths

    def _update_source_metadata(self, sources: list[SourceImage], metadata: list[Any], extra: dict[str, Any]) -> None:
        order = extra.get("order", [])
        ratios = extra.get("ratios", [])
        reference = extra.get("reference_index")
        order_by_index = {int(index): rank for rank, index in enumerate(order)}
        for idx, (source, item) in enumerate(zip(sources, metadata)):
            source.raw_format = item.raw_format
            source.camera_make = item.camera_make
            source.camera_model = item.camera_model
            source.lens_model = item.lens_model
            source.width = item.width
            source.height = item.height
            source.iso = item.iso
            source.aperture = item.aperture
            source.exposure_time = item.exposure_time
            source.exposure_bias = item.exposure_bias
            source.focal_length = item.focal_length
            source.black_level = item.black_level
            source.white_level = item.white_level
            source.cfa_pattern = item.cfa_pattern
            source.color_matrix = item.color_matrix
            source.camera_wb = item.camera_wb
            source.exposure_order = order_by_index.get(idx)
            source.relative_exposure_ratio = float(ratios[idx]) if idx < len(ratios) else None
            source.is_reference = idx == reference
            source.audit_status = "fail" if item.errors else ("warn" if item.warnings else "pass")
            source.audit_warnings = [*(item.warnings or []), *(item.errors or [])]
        self.db.commit()

    def _write_mask_artifacts(self, job: Job, source_masks: TypedSourceMaskResult) -> dict[str, str]:
        artifacts: dict[str, str] = {}
        for name, mask in source_masks.masks.items():
            artifacts[name] = self._write_mask_artifact(job, f"mask_{name}", f"working/{job.id}/masks/{name}.png", mask).id
        artifacts["source_core"] = self._write_mask_artifact(job, "mask_source_core", f"working/{job.id}/masks/source_core.png", source_masks.source_core).id
        return artifacts

    def _write_json_artifact(self, job: Job, artifact_type: str, storage_key: str, payload: dict[str, Any]):
        local = settings.scratch_root / job.id / Path(storage_key).name
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
        self.storage.put_file(local, storage_key, "application/json")
        return create_artifact(
            self.db,
            ArtifactCreate(job_id=job.id, image_set_id=job.image_set_id, artifact_type=artifact_type, storage_key=storage_key, mime_type="application/json", file_size=local.stat().st_size),
        )

    def _write_npy_artifact(self, job: Job, artifact_type: str, storage_key: str, array: np.ndarray):
        local = settings.scratch_root / job.id / Path(storage_key).name
        local.parent.mkdir(parents=True, exist_ok=True)
        np.save(local, array.astype(np.float32))
        self.storage.put_file(local, storage_key, "application/octet-stream")
        return create_artifact(self.db, ArtifactCreate(job_id=job.id, image_set_id=job.image_set_id, artifact_type=artifact_type, storage_key=storage_key, mime_type="application/octet-stream", file_size=local.stat().st_size))

    def _write_array_png_artifact(self, job: Job, artifact_type: str, storage_key: str, array: np.ndarray):
        local = settings.scratch_root / job.id / Path(storage_key).name
        local.parent.mkdir(parents=True, exist_ok=True)
        data = array.astype(np.float32)
        if data.ndim == 2:
            p99 = float(np.percentile(data, 99))
            if p99 > 1e-8:
                data = data / p99
            out = (np.clip(data, 0, 1) * 255).astype(np.uint8)
        else:
            out = (np.clip(data, 0, 1) * 255).astype(np.uint8)
        imageio.imwrite(local, out)
        self.storage.put_file(local, storage_key, "image/png")
        return create_artifact(self.db, ArtifactCreate(job_id=job.id, image_set_id=job.image_set_id, artifact_type=artifact_type, storage_key=storage_key, mime_type="image/png", file_size=local.stat().st_size))

    def _write_mask_artifact(self, job: Job, artifact_type: str, storage_key: str, mask: np.ndarray):
        return self._write_array_png_artifact(job, artifact_type, storage_key, mask.astype(np.float32))

    def _write_rgb_image_artifact(self, job: Job, artifact_type: str, storage_key: str, image: np.ndarray, mime_type: str, writer):
        local = settings.scratch_root / job.id / Path(storage_key).name
        writer(local)
        self.storage.put_file(local, storage_key, mime_type)
        h, w = image.shape[:2]
        return create_artifact(self.db, ArtifactCreate(job_id=job.id, image_set_id=job.image_set_id, artifact_type=artifact_type, storage_key=storage_key, mime_type=mime_type, width=w, height=h, file_size=local.stat().st_size))

    def _write_final_outputs(self, job: Job, selected_image: np.ndarray, hdr_base_rgb: np.ndarray, context: PipelineContext) -> dict[str, str]:
        final = self._write_rgb_image_artifact(job, "final_jpg", f"processed/{job.id}/final.jpg", selected_image, "image/jpeg", lambda path: write_jpeg(selected_image, path, context.config.jpeg_quality))
        png = self._write_rgb_image_artifact(job, "final_png", f"processed/{job.id}/final.png", selected_image, "image/png", lambda path: write_png(selected_image, path))
        webp = self._write_rgb_image_artifact(job, "final_webp", f"processed/{job.id}/final.webp", selected_image, "image/webp", lambda path: write_webp(selected_image, path, 90))
        tiff_local = settings.scratch_root / job.id / "final.tiff"
        write_tiff_float(hdr_base_rgb, tiff_local)
        self.storage.put_file(tiff_local, f"processed/{job.id}/final.tiff", "image/tiff")
        tiff = create_artifact(self.db, ArtifactCreate(job_id=job.id, image_set_id=job.image_set_id, artifact_type="final_tiff", storage_key=f"processed/{job.id}/final.tiff", mime_type="image/tiff", file_size=tiff_local.stat().st_size))
        return {"final_jpg": final.id, "final_png": png.id, "final_webp": webp.id, "final_tiff": tiff.id}

    def _require_job(self, job_id: str) -> Job:
        job = get_job(self.db, job_id)
        if job is None:
            raise RuntimeError(f"Job not found: {job_id}")
        return job

    def _context(self, job: Job) -> PipelineContext:
        return PipelineContext(job=job, config=config_from_snapshot(job.config_snapshot))
