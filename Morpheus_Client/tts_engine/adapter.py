"""Compatibility shim for the relocated Llama adapter.

The concrete implementation lives in :mod:`llama_local`.  This module
re-exports :class:`TTSAdapter` for any legacy imports using the old path.
"""

from .llama_local import TTSAdapter

__all__ = ["TTSAdapter"]

