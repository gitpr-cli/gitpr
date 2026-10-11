"""Infrastructure for the baseline: where `.gitpr/baseline.json` lives and how
it is read and written."""

from src.infrastructure.baseline.local_baseline_repository import (
    BASELINE_NAME,
    OVERRIDES_NAME,
    BaselineSnapshot,
    baseline_path,
    overrides_path,
    read_baseline,
    read_manifest,
    read_manifest_raw,
    read_overrides,
    write_manifest,
)

__all__ = [
    "BASELINE_NAME",
    "OVERRIDES_NAME",
    "BaselineSnapshot",
    "baseline_path",
    "overrides_path",
    "read_baseline",
    "read_manifest",
    "read_manifest_raw",
    "read_overrides",
    "write_manifest",
]
