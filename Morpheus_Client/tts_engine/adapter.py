"""Compatibility shim for the relocated Orpheus adapter.

The concrete implementation lives in :mod:`orpheus_local`.  This module
re-exports :class:`TTSAdapter` for any legacy imports using the old path.
"""

from .orpheus_local import TTSAdapter

__all__ = ["TTSAdapter"]

