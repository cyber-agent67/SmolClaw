"""Vision subsystem — AI-powered page analysis and settings extraction."""

from .client import VisionClient
from .extractor import ExtractionWorker

__all__ = ["VisionClient", "ExtractionWorker"]
