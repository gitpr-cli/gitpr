"""Package marker for external linter & SAST bridges."""
from src.domain.finding.finding_types import NormalizedFinding
from src.infrastructure.linter.external.base_bridge import (
    ExternalLinterBridge,
    ExternalLinterResult,
)

__all__ = ["ExternalLinterBridge", "ExternalLinterResult", "NormalizedFinding"]

