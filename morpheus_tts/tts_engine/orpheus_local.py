from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Tuple

from orpheus_tts.engine_class import OrpheusModel
from .speechpipe import tokens_decoder

# Lock to protect concurrent initialisation
_model_lock = asyncio.Lock()


@lru_cache(maxsize=1)
def _load_model_impl(model_name: str = "medium-3b", **kwargs) -> Tuple[OrpheusModel, callable]:
    """Load the Orpheus model and return it with the token decoder.

    The :func:`functools.lru_cache` decorator ensures that the heavy
    model and decoder session are constructed only once per process and
    subsequent calls reuse the cached objects.
    """
    model = OrpheusModel(model_name, **kwargs)
    return model, tokens_decoder


async def _load_model(model_name: str = "medium-3b", **kwargs) -> Tuple[OrpheusModel, callable]:
    """Asynchronously load and cache the model.

    Concurrent callers are serialised via an :class:`asyncio.Lock` to
    avoid duplicated initialisation work when the first request arrives
    from multiple tasks simultaneously.
    """
    async with _model_lock:
        return _load_model_impl(model_name, **kwargs)
