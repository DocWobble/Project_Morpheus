"""Registry for text source adapters."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Type

from . import TextSource


@dataclass
class _SourceSpec:
    constructor: Type[TextSource]
    describe: Callable[[], Dict[str, Any]]


class SourceRegistry:
    """Simple registry for text sources."""

    def __init__(self) -> None:
        self._registry: Dict[str, _SourceSpec] = {}

    def register(
        self, name: str, constructor: Type[TextSource], describe: Callable[[], Dict[str, Any]]
    ) -> None:
        self._registry[name] = _SourceSpec(constructor, describe)

    def available(self) -> Dict[str, Dict[str, Any]]:
        """Return capability descriptors for all registered sources."""

        return {name: spec.describe() for name, spec in self._registry.items()}

    def create(self, name: str, **kwargs: Any) -> TextSource:
        """Instantiate a source by name."""

        spec = self._registry[name]
        return spec.constructor(**kwargs)


from .websocket import WebSocketSource, describe as ws_describe
from .http_poll import HTTPPollingSource, describe as http_describe
from .cli_pipe import CLIPipeSource, describe as cli_describe

# Global registry instance pre-populated with the built-in sources
registry = SourceRegistry()
registry.register("websocket", WebSocketSource, ws_describe)
registry.register("http_poll", HTTPPollingSource, http_describe)
registry.register("cli_pipe", CLIPipeSource, cli_describe)

__all__ = ["registry", "SourceRegistry"]
