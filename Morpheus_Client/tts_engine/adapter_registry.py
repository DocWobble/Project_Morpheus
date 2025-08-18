from __future__ import annotations

"""Registry of available TTS adapters.

Each adapter provides a :func:`describe` method to advertise its
capabilities and a voice mapping function that projects the abstract
voice schema into backend specific parameters.  The registry exposes a
simple factory for constructing adapters by name which is used by the
FastAPI application to enable hot swapping of engines at runtime.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, Type

from pydantic import BaseModel

from .adapter import TTSAdapter as OrpheusAdapter
from .inference import AVAILABLE_VOICES, DEFAULT_VOICE


class VoiceSchema(BaseModel):
    """Backend agnostic description of a voice.

    Only the ``voice`` field is currently used by the bundled Orpheus
    adapter, but the schema intentionally leaves room for richer
    descriptors so other backends can map timbre, prosody or accent as
    needed.
    """

    voice: str | None = None
    timbre: str | None = None
    prosody: str | None = None
    accent: str | None = None
    emotion_priors: str | None = None
    pace: str | None = None


def _orpheus_voice_mapper(schema: VoiceSchema) -> Dict[str, Any]:
    """Map a :class:`VoiceSchema` to Orpheus adapter parameters."""

    voice = schema.voice or schema.timbre or DEFAULT_VOICE
    if voice not in AVAILABLE_VOICES:
        voice = DEFAULT_VOICE
    return {"voice": voice}


def _orpheus_describe() -> Dict[str, Any]:
    """Return capability descriptor for the Orpheus adapter."""

    return {
        "name": "orpheus",
        "streaming": True,
        "unit": "ms",
        "granularity": [8, 12, 16, 24, 32, 48, 64],
        "voices": AVAILABLE_VOICES,
        "supports_barge_in": True,
        "supports_seed": False,
        "stateful_context": "minimal",
    }


@dataclass
class _AdapterSpec:
    constructor: Type
    describe: Callable[[], Dict[str, Any]]
    voice_mapper: Callable[[VoiceSchema], Dict[str, Any]]


class AdapterRegistry:
    """Simple registry for synthesis adapters."""

    def __init__(self) -> None:
        self._registry: Dict[str, _AdapterSpec] = {}

    def register(
        self,
        name: str,
        constructor: Type,
        describe: Callable[[], Dict[str, Any]],
        voice_mapper: Callable[[VoiceSchema], Dict[str, Any]],
    ) -> None:
        self._registry[name] = _AdapterSpec(constructor, describe, voice_mapper)

    def available(self) -> Dict[str, Dict[str, Any]]:
        """Return capability descriptions for all adapters."""

        return {name: spec.describe() for name, spec in self._registry.items()}

    def create(
        self, name: str, *, prompt: str, voice: VoiceSchema, **kwargs: Any
    ):
        """Instantiate an adapter by name."""

        spec = self._registry[name]
        params = spec.voice_mapper(voice)
        params.update(kwargs)
        return spec.constructor(prompt=prompt, **params)


# Global registry instance pre-populated with the default Orpheus adapter
registry = AdapterRegistry()
registry.register(
    "orpheus", OrpheusAdapter, _orpheus_describe, _orpheus_voice_mapper
)

__all__ = ["VoiceSchema", "AdapterRegistry", "registry"]
