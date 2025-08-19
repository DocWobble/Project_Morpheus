"""ASGI server for Morpheus built on Starlette.

This module provides a lightweight HTTP and WebSocket interface around the
text‑to‑speech orchestrator.  It replaces the previous FastAPI implementation
with a minimal Starlette router while preserving the public routes so existing
clients continue to function.
"""

from __future__ import annotations

import asyncio
import struct
from contextlib import suppress
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect

from .config import ensure_env_file_exists, get_current_config, save_config
from .tts_engine import AVAILABLE_VOICES, DEFAULT_VOICE
from .tts_engine.adapter_registry import VoiceSchema, registry as adapter_registry
from .tts_engine.inference import SAMPLE_RATE
from .orchestrator.buffer import PlaybackBuffer
from .orchestrator.chunk_ladder import ChunkLadder
from .orchestrator.core import Orchestrator
from .orchestrator.stitcher import stitch_chunks
from text_sources import TextSource
from text_sources.registry import registry as source_registry

# Ensure environment is initialized
ensure_env_file_exists()
load_dotenv(override=True)


def riff_header(sample_rate: int = SAMPLE_RATE) -> bytes:
    """Return a generic RIFF/WAVE header with unknown length."""

    byte_rate = sample_rate * 2
    return struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        0xFFFFFFFF,
        b"WAVE",
        b"fmt ",
        16,
        1,
        1,
        sample_rate,
        byte_rate,
        2,
        16,
        b"data",
        0xFFFFFFFF,
    )


async def wav_streamer(pcm_iter, sample_rate: int = SAMPLE_RATE):
    """Wrap a PCM iterator with a WAV header for streaming."""

    yield riff_header(sample_rate)
    async for chunk in pcm_iter:
        yield chunk


async def websocket_pcm_stream(
    websocket: WebSocket, pcm_iter, sample_rate: int = SAMPLE_RATE
) -> None:
    """Send a WAV header followed by PCM frames over a WebSocket."""

    await websocket.send_bytes(riff_header(sample_rate))
    async for chunk in pcm_iter:
        await websocket.send_bytes(chunk)


# Global orchestrator state for barge-in
current_orchestrator: Orchestrator | None = None
current_adapter_name = "orpheus"
current_voice = VoiceSchema(voice=DEFAULT_VOICE)
current_source_name = "cli_pipe"
current_source: TextSource | None = None
current_source_task: asyncio.Task | None = None


async def _consume_source(source: TextSource) -> None:
    """Continuously feed text from a source into the orchestrator."""

    try:
        async for text in source.stream():
            pcm_stream = orchestrated_pcm_stream(prompt=text, voice=None)
            async for _ in pcm_stream:
                pass
    except asyncio.CancelledError:  # pragma: no cover - task cancel
        pass


async def init_source(name: str, **options: Any) -> None:
    """Instantiate and begin consuming from a text source."""

    global current_source_name, current_source, current_source_task
    current_source_name = name
    if name == "cli_pipe" and "reader" not in options:
        options["reader"] = asyncio.StreamReader()
    source = source_registry.create(name, **options)
    current_source = source
    if current_source_task:
        current_source_task.cancel()
        with suppress(asyncio.CancelledError):
            await current_source_task
    current_source_task = asyncio.create_task(_consume_source(source))


async def orchestrated_pcm_stream(
    prompt: str,
    voice: str | VoiceSchema | None,
    *,
    adapter_name: str | None = None,
    use_batching: bool = False,
    max_batch_chars: int = 1000,
):
    """Create an orchestrator-driven PCM stream."""

    global current_orchestrator
    name = adapter_name or current_adapter_name
    schema = (
        current_voice
        if voice is None
        else (VoiceSchema(voice=voice) if isinstance(voice, str) else voice)
    )
    adapter = adapter_registry.create(
        name,
        prompt=prompt,
        voice=schema,
        use_batching=use_batching,
        max_batch_chars=max_batch_chars,
    )
    buffer = PlaybackBuffer(capacity_ms=1000)
    current_orchestrator = Orchestrator(adapter, buffer, ChunkLadder())
    stitched = stitch_chunks(
        current_orchestrator.stream(), sample_rate=SAMPLE_RATE
    )
    async for chunk in stitched:
        yield chunk.pcm


class SpeechRequest(BaseModel):
    input: str
    model: str = "orpheus"
    voice: str = DEFAULT_VOICE
    response_format: str = "wav"
    speed: float = 1.0


async def create_speech_api(request: Request) -> StreamingResponse:
    """Generate speech from text via orchestrator."""

    try:
        payload = SpeechRequest(**await request.json())
    except ValidationError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not payload.input:
        raise HTTPException(status_code=400, detail="Missing input text")

    use_batching = len(payload.input) > 1000
    pcm_stream = orchestrated_pcm_stream(
        prompt=payload.input,
        voice=payload.voice,
        use_batching=use_batching,
        max_batch_chars=1000,
    )
    return StreamingResponse(
        wav_streamer(pcm_stream, sample_rate=SAMPLE_RATE),
        media_type="audio/wav",
    )


async def list_voices(request: Request) -> JSONResponse:  # pragma: no cover - simple
    """Return list of available voices."""

    if not AVAILABLE_VOICES:
        raise HTTPException(status_code=404, detail="No voices available")
    return JSONResponse({"status": "ok", "voices": AVAILABLE_VOICES})


async def tts_ws(websocket: WebSocket) -> None:
    """Stream synthesized audio over WebSocket."""

    await websocket.accept()
    try:
        prompt = websocket.query_params.get("prompt") or ""
        if not prompt:
            await websocket.close(code=1008)
            return
        voice = websocket.query_params.get("voice")
        pcm_stream = orchestrated_pcm_stream(prompt=prompt, voice=voice)
        await websocket_pcm_stream(websocket, pcm_stream, sample_rate=SAMPLE_RATE)
    except WebSocketDisconnect:  # pragma: no cover - network race
        pass


async def get_adapters(request: Request) -> JSONResponse:
    """Expose capability descriptors for all available adapters."""

    return JSONResponse(adapter_registry.available())


async def get_sources(request: Request) -> JSONResponse:
    """Expose capability descriptors for all registered text sources."""

    return JSONResponse(source_registry.available())


async def get_config(request: Request) -> JSONResponse:
    """Return current configuration from environment and `.env`."""

    return JSONResponse(get_current_config())


async def update_config(request: Request) -> JSONResponse:
    """Update configuration and persist changes to `.env`."""

    global current_adapter_name, current_voice

    try:
        data = await request.json()
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    adapter = data.get("adapter")
    if adapter:
        available = adapter_registry.available()
        if adapter not in available:
            raise HTTPException(status_code=404, detail="Unknown adapter")
        current_adapter_name = adapter

    voice = data.get("voice")
    if voice:
        if isinstance(voice, dict):
            current_voice = VoiceSchema(**voice)
        else:
            current_voice = VoiceSchema(voice=voice)

    source = data.get("source")
    source_cfg = data.get("source_config", {})
    if source:
        sources = source_registry.available()
        if source not in sources:
            raise HTTPException(status_code=404, detail="Unknown source")
        await init_source(source, **source_cfg)
    elif source_cfg and current_source_name:
        await init_source(current_source_name, **source_cfg)

    if current_orchestrator:
        current_orchestrator.signal_barge_in()

    env_cfg = get_current_config()
    persist = {k: v for k, v in data.items() if k != "source_config"}
    if voice:
        persist["voice"] = current_voice.voice
    env_cfg.update({k: str(v) if not isinstance(v, str) else v for k, v in persist.items()})
    save_config(env_cfg)

    resp = {"message": "ok"}
    if "adapter" in env_cfg:
        resp["adapter"] = env_cfg["adapter"]
    if "voice" in env_cfg:
        resp["voice"] = current_voice.model_dump()
    if "source" in env_cfg:
        resp["source"] = env_cfg["source"]
    return JSONResponse(resp)


async def stats(request: Request) -> JSONResponse:
    """Return the current orchestrator timeline for live monitoring."""

    timeline = [] if current_orchestrator is None else current_orchestrator.timeline
    return JSONResponse({"timeline": timeline})


async def barge_in(request: Request) -> JSONResponse:  # pragma: no cover - simple
    if current_orchestrator:
        current_orchestrator.signal_barge_in()
    return JSONResponse({"status": "ok"})


async def barge_in_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            await websocket.receive_text()
            if current_orchestrator:
                current_orchestrator.signal_barge_in()
                await websocket.send_text("ok")
    except WebSocketDisconnect:  # pragma: no cover - network race
        pass


routes = [
    Route("/v1/audio/speech", create_speech_api, methods=["POST"]),
    Route("/v1/audio/voices", list_voices, methods=["GET"]),
    WebSocketRoute("/ws/tts", tts_ws),
    Route("/adapters", get_adapters, methods=["GET"]),
    Route("/sources", get_sources, methods=["GET"]),
    Route("/stats", stats, methods=["GET"]),
    Route("/config", get_config, methods=["GET"]),
    Route("/config", update_config, methods=["POST"]),
    Route("/barge-in", barge_in, methods=["POST"]),
    WebSocketRoute("/ws/barge-in", barge_in_ws),
    Mount(
        "/admin",
        app=StaticFiles(directory=Path(__file__).resolve().parent / "admin", html=True),
        name="admin",
    ),
]


app = Starlette(routes=routes)


def start_server(host: str = "0.0.0.0", port: int = 5005) -> None:
    """Start the Morpheus client API and admin server using uvicorn."""

    import uvicorn

    uvicorn.run(app, host=host, port=port)

