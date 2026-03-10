"""Backward-compatible shim that forwards calls to EIM architecture."""

from agentic_navigator.main import cleanup_resources, run_agent_with_args

__all__ = ["run_agent_with_args", "cleanup_resources"]
