import sys
import types

# Provide lightweight stubs for optional native dependencies
sys.modules.setdefault("sounddevice", types.SimpleNamespace())

class _Torch(types.SimpleNamespace):
    def __init__(self):
        cuda = types.SimpleNamespace(is_available=lambda: False, Stream=lambda: None)
        backends = types.SimpleNamespace(mps=types.SimpleNamespace(is_available=lambda: False))
        super().__init__(cuda=cuda, backends=backends)

sys.modules.setdefault("torch", _Torch())


class _SNAC:
    @classmethod
    def from_pretrained(cls, *args, **kwargs):  # pragma: no cover - simple stub
        return cls()

    def eval(self):
        return self

    def to(self, *args, **kwargs):  # noqa: D401
        return self

    def decode(self, codes):
        return types.SimpleNamespace()

sys.modules.setdefault("snac", types.SimpleNamespace(SNAC=_SNAC))
