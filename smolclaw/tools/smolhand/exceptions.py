"""Exception hierarchy for browser subagents.

This module provides a structured exception hierarchy for all browser subagent
operations, organized by layer.
"""

from __future__ import annotations


class BrowserSubAgentError(Exception):
    """Base exception for all browser subagent errors."""


# =============================================================================
# Layer 1 Exceptions (Raw Browser Access)
# =============================================================================


class BrowserLayerError(BrowserSubAgentError):
    """Error in Layer 1 (raw browser access) operations."""


class PageNotLoadedError(BrowserLayerError):
    """Raised when page content is not available."""


class BrowserDriverError(BrowserLayerError):
    """Raised when browser driver is not initialized or fails."""


class LinkExtractionError(BrowserLayerError):
    """Raised when hyperlink extraction fails."""


# =============================================================================
# Layer 2 Exceptions (Vision)
# =============================================================================


class VisionLayerError(BrowserSubAgentError):
    """Error in Layer 2 (vision) operations."""


class FlorenceModelError(VisionLayerError):
    """Raised when Florence model fails to load or process."""


class ScreenshotError(VisionLayerError):
    """Raised when screenshot capture fails."""


class VisionAnalysisError(VisionLayerError):
    """Raised when vision analysis fails."""


# =============================================================================
# Layer 3 Exceptions (DOM Exploration)
# =============================================================================


class ExplorationLayerError(BrowserSubAgentError):
    """Error in Layer 3 (DOM exploration) operations."""


class ExplorationError(ExplorationLayerError):
    """Raised when A* exploration fails."""


class LinkRankingError(ExplorationLayerError):
    """Raised when link ranking fails."""


class ScoutError(ExplorationLayerError):
    """Raised when scout lookahead fails."""


# =============================================================================
# Layer 4 Exceptions (Q-Learning)
# =============================================================================


class QLearningLayerError(BrowserSubAgentError):
    """Error in Layer 4 (Q-learning) operations."""


class QValueError(QLearningLayerError):
    """Raised when Q-value computation fails."""


class TaskScoringError(QLearningLayerError):
    """Raised when task scoring fails."""


class VectorizationError(QLearningLayerError):
    """Raised when text vectorization fails."""


# =============================================================================
# General Exceptions
# =============================================================================


class TabNotFoundError(BrowserSubAgentError):
    """Raised when a tab cannot be found or switched to."""


class NavigationError(BrowserSubAgentError):
    """Raised when navigation fails."""


class ConfigurationError(BrowserSubAgentError):
    """Raised when configuration is invalid or missing."""


class TimeoutError(BrowserSubAgentError):
    """Raised when an operation times out."""


__all__ = [
    # Base
    "BrowserSubAgentError",
    # Layer 1
    "BrowserLayerError",
    "PageNotLoadedError",
    "BrowserDriverError",
    "LinkExtractionError",
    # Layer 2
    "VisionLayerError",
    "FlorenceModelError",
    "ScreenshotError",
    "VisionAnalysisError",
    # Layer 3
    "ExplorationLayerError",
    "ExplorationError",
    "LinkRankingError",
    "ScoutError",
    # Layer 4
    "QLearningLayerError",
    "QValueError",
    "TaskScoringError",
    "VectorizationError",
    # General
    "TabNotFoundError",
    "NavigationError",
    "ConfigurationError",
    "TimeoutError",
]
