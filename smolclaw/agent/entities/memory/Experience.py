"""Backward-compat shim — canonical location is core/memory/store.py."""

from core.memory.store import Experience, from_dict, to_dict

__all__ = ["Experience", "from_dict", "to_dict"]
