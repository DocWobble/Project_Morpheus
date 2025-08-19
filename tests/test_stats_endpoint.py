import asyncio
import importlib.util
import os
import sys
from pathlib import Path

import httpx

# Ensure repo root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Morpheus_Client.orchestrator.adapter import AudioChunk, TTSAdapter
from Morpheus_Client.orchestrator.buffer import PlaybackBuffer
from Morpheus_Client.orchestrator.chunk_ladder import ChunkLadder
from Morpheus_Client.orchestrator.core import Orchestrator


def load_app():
    spec = importlib.util.spec_from_file_location(
        "orfastapi_app", Path("Orpheus-FastAPI/app.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DummyAdapter(TTSAdapter):
    def __init__(self, chunks):
        self.chunks = list(chunks)

    async def pull(self, _size):
        if self.chunks:
            return self.chunks.pop(0)
        return AudioChunk(pcm=b"", duration_ms=0, eos=True)

    async def reset(self):
        pass


def test_stats_endpoint_exposes_timeline():
    module = load_app()
    adapter = DummyAdapter([AudioChunk(pcm=b"", duration_ms=10, eos=True)])
    orch = Orchestrator(adapter, PlaybackBuffer(capacity_ms=500), ChunkLadder())
    module.current_orchestrator = orch

    async def run():
        async for _ in orch.stream():
            pass

    asyncio.run(run())

    async def fetch():
        transport = httpx.ASGITransport(app=module.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/stats")

    resp = asyncio.run(fetch())
    assert resp.status_code == 200
    body = resp.json()
    assert "timeline" in body
    assert isinstance(body["timeline"], list)
