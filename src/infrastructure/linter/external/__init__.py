"""Package marker for external linter & SAST bridges."""
from src.infrastructure.linter.external.base_bridge import (
    ExternalLinterBridge,
    ExternalLinterResult,
    NormalizedFinding,
)

__all__ = ["ExternalLinterBridge", "ExternalLinterResult", "NormalizedFinding"]

