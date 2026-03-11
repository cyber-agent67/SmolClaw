"""Metrics and observability for browser subagents.

This module provides metrics collection and latency measurement for all
browser subagent operations.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point.

    Attributes:
        name: Metric name
        value: Metric value
        tags: Metric tags for filtering/grouping
        timestamp: Unix timestamp when metric was recorded
    """
    name: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """Collects and reports metrics for browser subagents.

    Supports three metric types:
    - Counters: Incremental values (e.g., request count)
    - Gauges: Point-in-time values (e.g., current connections)
    - Histograms: Distribution of values (e.g., latency)
    """

    def __init__(self) -> None:
        """Initialize the metrics collector."""
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}

    def increment(
        self,
        name: str,
        value: int = 1,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Increment a counter metric.

        Args:
            name: Metric name
            value: Amount to increment by
            tags: Optional tags for filtering/grouping
        """
        key = self._make_key(name, tags)
        self._counters[key] = self._counters.get(key, 0) + value

    def gauge(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Set a gauge metric.

        Args:
            name: Metric name
            value: Gauge value
            tags: Optional tags for filtering/grouping
        """
        key = self._make_key(name, tags)
        self._gauges[key] = value

    def histogram(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a histogram metric.

        Args:
            name: Metric name
            value: Value to record
            tags: Optional tags for filtering/grouping
        """
        key = self._make_key(name, tags)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)

    def _make_key(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
    ) -> str:
        """Create metric key from name and tags.

        Args:
            name: Metric name
            tags: Optional tags

        Returns:
            Metric key string
        """
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"

    def snapshot(self) -> Dict[str, Any]:
        """Return current metrics snapshot.

        Returns:
            Dictionary with counters, gauges, and histogram statistics
        """
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                k: {
                    "count": len(v),
                    "sum": sum(v),
                    "avg": sum(v) / len(v) if v else 0.0,
                    "min": min(v) if v else 0.0,
                    "max": max(v) if v else 0.0,
                }
                for k, v in self._histograms.items()
            },
            "timestamp": time.time(),
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()

    def get_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> int:
        """Get current counter value.

        Args:
            name: Metric name
            tags: Optional tags

        Returns:
            Counter value or 0 if not found
        """
        key = self._make_key(name, tags)
        return self._counters.get(key, 0)

    def get_gauge(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get current gauge value.

        Args:
            name: Metric name
            tags: Optional tags

        Returns:
            Gauge value or None if not found
        """
        key = self._make_key(name, tags)
        return self._gauges.get(key)


# Global metrics collector
_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get or create the global metrics collector.

    Returns:
        Global MetricsCollector instance
    """
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics


def reset_metrics() -> MetricsCollector:
    """Reset and return the global metrics collector.

    Returns:
        New MetricsCollector instance
    """
    global _metrics
    _metrics = MetricsCollector()
    return _metrics


@contextmanager
def measure_latency(
    metric_name: str,
    tags: Optional[Dict[str, str]] = None,
    log_level: int = logging.DEBUG,
):
    """Context manager to measure operation latency.

    Usage:
        with measure_latency("layer1.read_page"):
            result = ReadCurrentPage.execute()

    Args:
        metric_name: Base name for latency metrics
        tags: Optional tags for filtering/grouping
        log_level: Logging level for latency output
    """
    start = time.perf_counter()
    success = True
    try:
        yield
        get_metrics().increment(f"{metric_name}.success", tags=tags)
    except Exception:
        success = False
        get_metrics().increment(f"{metric_name}.error", tags=tags)
        raise
    finally:
        elapsed = time.perf_counter() - start
        get_metrics().histogram(f"{metric_name}.latency", elapsed, tags=tags)
        logger.log(
            log_level,
            "%s completed in %.3fs (success=%s)",
            metric_name,
            elapsed,
            success,
        )


def record_operation(
    operation: str,
    layer: str,
    success: bool = True,
    duration: Optional[float] = None,
    extra_tags: Optional[Dict[str, str]] = None,
) -> None:
    """Record a generic operation metric.

    Args:
        operation: Operation name
        layer: Layer name (layer1, layer2, layer3, layer4)
        success: Whether operation succeeded
        duration: Optional operation duration in seconds
        extra_tags: Optional additional tags
    """
    tags = {"layer": layer, **(extra_tags or {})}

    if success:
        get_metrics().increment(f"{layer}.{operation}.success", tags=tags)
    else:
        get_metrics().increment(f"{layer}.{operation}.error", tags=tags)

    if duration is not None:
        get_metrics().histogram(f"{layer}.{operation}.latency", duration, tags=tags)


__all__ = [
    "MetricPoint",
    "MetricsCollector",
    "get_metrics",
    "reset_metrics",
    "measure_latency",
    "record_operation",
]
