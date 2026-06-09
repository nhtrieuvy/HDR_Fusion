from __future__ import annotations

DEFAULT_CFA = ("R", "G", "G", "B")


def normalize_cfa_pattern(pattern) -> tuple[str, str, str, str]:
    if not pattern:
        return DEFAULT_CFA
    values = tuple(str(item).upper()[0] for item in pattern)
    if len(values) >= 4 and set(values[:4]).issubset({"R", "G", "B"}):
        return values[:4]  # type: ignore[return-value]
    return DEFAULT_CFA

