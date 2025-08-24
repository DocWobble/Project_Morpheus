import os
import sys
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Stub optional dependency to avoid import errors
sys.modules.setdefault("sounddevice", types.SimpleNamespace())

import asyncio

from Morpheus_Client.tts_engine.orpheus_local import _stream_from_model


class DummyChunk:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def tobytes(self) -> bytes:
        return self._data


class NoneTerminatingIterator:
    def __init__(self) -> None:
        self._items = [
            (16000, DummyChunk(b"a")),
            (16000, DummyChunk(b"b")),
        ]

    def __iter__(self):
        return self

    def __next__(self):
        if self._items:
            return self._items.pop(0)
        return None


class DummyModel:
    def stream_tts_sync(self, *_: object, **__: object):
        return NoneTerminatingIterator()

def test_stream_from_model_stops_on_none():
    model = DummyModel()

    async def run():
        gen = _stream_from_model(model, "hi", "voice")
        return [pcm async for pcm in gen]

    chunks = asyncio.run(run())
    assert chunks == [b"a", b"b"]
