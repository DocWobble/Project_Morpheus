import struct

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from .tts_engine import DEFAULT_VOICE
from .tts_engine.inference import SAMPLE_RATE
from .tts_engine.adapter_registry import VoiceSchema, registry as adapter_registry
from .orchestrator.core import Orchestrator
from .orchestrator.buffer import PlaybackBuffer
from .orchestrator.chunk_ladder import ChunkLadder
from .orchestrator.stitcher import stitch_chunks


def riff_header(sample_rate: int = SAMPLE_RATE) -> bytes:
    """Return a generic RIFF/WAVE header with unknown length."""
    byte_rate = sample_rate * 2
    return struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        0xFFFFFFFF,
        b'WAVE',
        b'fmt ',
        16,
        1,
        1,
        sample_rate,
        byte_rate,
        2,
        16,
        b'data',
        0xFFFFFFFF,
    )


async def wav_streamer(pcm_iter, sample_rate: int = SAMPLE_RATE):
    """Wrap a PCM iterator with a WAV header for streaming."""
    yield riff_header(sample_rate)
    async for chunk in pcm_iter:
        yield chunk


async def websocket_pcm_stream(websocket: WebSocket, pcm_iter, sample_rate: int = SAMPLE_RATE):
    """Send a WAV header followed by PCM frames over a WebSocket."""
    await websocket.send_bytes(riff_header(sample_rate))
    async for chunk in pcm_iter:
        await websocket.send_bytes(chunk)


# Global orchestrator state for barge-in
current_orchestrator: Orchestrator | None = None
current_adapter_name = "orpheus"
current_voice = VoiceSchema(voice=DEFAULT_VOICE)


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
        current_orchestrator.stream(),
        sample_rate=SAMPLE_RATE,
    )
    async for chunk in stitched:
        yield chunk.pcm


# FastAPI application
app = FastAPI(title="Core TTS Service")


class SpeechRequest(BaseModel):
    input: str
    model: str = "orpheus"
    voice: str = DEFAULT_VOICE
    response_format: str = "wav"
    speed: float = 1.0


class ConfigUpdate(BaseModel):
    adapter: str | None = None
    voice: VoiceSchema | None = None


@app.post("/v1/audio/speech")
async def create_speech_api(request: SpeechRequest):
    """Generate speech from text via orchestrator."""
    if not request.input:
        raise HTTPException(status_code=400, detail="Missing input text")
    use_batching = len(request.input) > 1000
    pcm_stream = orchestrated_pcm_stream(
        prompt=request.input,
        voice=request.voice,
        use_batching=use_batching,
        max_batch_chars=1000,
    )
    return StreamingResponse(
        wav_streamer(pcm_stream, sample_rate=SAMPLE_RATE),
        media_type="audio/wav",
    )


@app.websocket("/ws/tts")
async def tts_ws(websocket: WebSocket, prompt: str, voice: str | None = None):
    """Stream synthesized audio over WebSocket."""
    await websocket.accept()
    try:
        pcm_stream = orchestrated_pcm_stream(prompt=prompt, voice=voice)
        await websocket_pcm_stream(websocket, pcm_stream, sample_rate=SAMPLE_RATE)
    except WebSocketDisconnect:
        pass


@app.get("/adapters")
async def get_adapters():
    """Expose capability descriptors for all available adapters."""
    return adapter_registry.available()


@app.post("/config")
async def update_config(cfg: ConfigUpdate):
    """Update active adapter or voice schema."""
    global current_adapter_name, current_voice
    available = adapter_registry.available()
    if cfg.adapter:
        if cfg.adapter not in available:
            raise HTTPException(status_code=404, detail="Unknown adapter")
        current_adapter_name = cfg.adapter
    if cfg.voice:
        current_voice = cfg.voice
    if current_orchestrator:
        current_orchestrator.signal_barge_in()
    return {
        "adapter": current_adapter_name,
        "voice": current_voice.dict(),
    }


@app.post("/barge-in")
async def barge_in():
    if current_orchestrator:
        current_orchestrator.signal_barge_in()
    return JSONResponse(content={"status": "ok"})


@app.websocket("/ws/barge-in")
async def barge_in_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.receive_text()
            if current_orchestrator:
                current_orchestrator.signal_barge_in()
                await websocket.send_text("ok")
    except WebSocketDisconnect:
        pass


def start_server(host: str = "0.0.0.0", port: int = 5005) -> None:
    """Start the Morpheus TTS FastAPI server using uvicorn."""
    import uvicorn

    uvicorn.run(app, host=host, port=port)
