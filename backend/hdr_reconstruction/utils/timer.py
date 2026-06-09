from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter
from typing import Iterator


@dataclass(slots=True)
class Timer:
    elapsed: float = 0.0


@contextmanager
def timed() -> Iterator[Timer]:
    timer = Timer()
    start = perf_counter()
    try:
        yield timer
    finally:
        timer.elapsed = perf_counter() - start

