from __future__ import annotations

import numpy as np


def raw_luminance(raw: np.ndarray) -> np.ndarray:
    data = np.asarray(raw, dtype=np.float32)
    if data.ndim == 2:
        return data
    if data.ndim == 3:
        channels = data.shape[-1]
        if channels >= 3:
            return (0.2126 * data[..., 0] + 0.7152 * data[..., 1] + 0.0722 * data[..., 2]).astype(np.float32)
        return np.mean(data, axis=-1).astype(np.float32)
    raise ValueError(f"raw frame must be 2D mosaic or 3D multichannel, got shape={data.shape}")


def raw_luminance_stack(stack: np.ndarray) -> np.ndarray:
    data = np.asarray(stack, dtype=np.float32)
    if data.ndim == 3:
        return data
    if data.ndim == 4:
        return np.stack([raw_luminance(frame) for frame in data], axis=0).astype(np.float32)
    raise ValueError(f"raw stack must be 3D mosaic stack or 4D multichannel stack, got shape={data.shape}")


def expand_spatial_mask(mask: np.ndarray, target: np.ndarray) -> np.ndarray:
    spatial = np.asarray(mask).astype(bool)
    if target.ndim == 2:
        return spatial
    if target.ndim == 3:
        return spatial[..., None]
    if target.ndim == 4:
        return spatial[:, :, :, None]
    raise ValueError(f"unsupported target shape for mask broadcast: {target.shape}")
