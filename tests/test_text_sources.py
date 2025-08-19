import asyncio
import os
import asyncio
import os
import sys
import types

import httpx
import websockets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.modules.setdefault("sounddevice", types.SimpleNamespace())

from text_sources.cli_pipe import CLIPipeSource
from text_sources.http_poll import HTTPPollingSource
from text_sources.websocket import WebSocketSource
from Morpheus_Client.server import app


def test_cli_pipe_source():
    async def run():
        reader = asyncio.StreamReader()
        reader.feed_data(b"hello\nworld\n")
        reader.feed_eof()
        source = CLIPipeSource(reader)
        out = []
        async for msg in source.stream():
            out.append(msg)
        return out

    assert asyncio.run(run()) == ["hello", "world"]


def test_http_poll_source():
    messages = ["first", "second"]

    def handler(request):
        if messages:
            return httpx.Response(200, text=messages.pop(0))
        return httpx.Response(200, text="")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    source = HTTPPollingSource("http://test", client=client)

    async def run():
        out = []
        async for msg in source.stream():
            out.append(msg)
        return out

    assert asyncio.run(run()) == ["first", "second"]


def test_websocket_source():
    async def run():
        async def ws_handler(websocket):
            await websocket.send("one")
            await websocket.send("two")
            await websocket.close()

        async with websockets.serve(ws_handler, "localhost", 0) as server:
            port = server.sockets[0].getsockname()[1]
            source = WebSocketSource(f"ws://localhost:{port}")
            out = []
            async for msg in source.stream():
                out.append(msg)
        return out

    assert asyncio.run(run()) == ["one", "two"]


def test_config_updates_source():
    async def run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/config", json={"source": "cli_pipe"})
            return resp

    resp = asyncio.run(run())
    assert resp.status_code == 200
    assert resp.json()["source"] == "cli_pipe"
