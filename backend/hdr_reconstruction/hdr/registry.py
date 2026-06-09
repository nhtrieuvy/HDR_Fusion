from __future__ import annotations

from hdr_reconstruction.hdr.base import HDRAlgorithm
from hdr_reconstruction.hdr.linear_rgb_merge import LinearRGBMerge
from hdr_reconstruction.hdr.noise_aware_weighted_linear_hdr_merge import NoiseAwareWeightedLinearHDRMerge
from hdr_reconstruction.hdr.raw_domain_weighted_hdr_merge import RawDomainWeightedHDRMerge
from hdr_reconstruction.hdr.weighted_linear_rgb_merge import WeightedLinearRGBMerge


def algorithm_registry() -> dict[str, HDRAlgorithm]:
    algorithms: list[HDRAlgorithm] = [
        LinearRGBMerge(),
        WeightedLinearRGBMerge(),
        NoiseAwareWeightedLinearHDRMerge(),
        RawDomainWeightedHDRMerge(),
    ]
    return {algorithm.name: algorithm for algorithm in algorithms}


def get_algorithms(names: list[str]) -> list[HDRAlgorithm]:
    registry = algorithm_registry()
    missing = [name for name in names if name not in registry]
    if missing:
        raise ValueError(f"Unknown HDR algorithms: {', '.join(missing)}")
    return [registry[name] for name in names]
