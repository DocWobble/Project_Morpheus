---

# PROJECT MORPHEUS → Real-Time, Backend-Agnostic TTS

## Mission

Refactor the entire repo (which includes the main Orpheus TTS pretrained model as well as its primary local API client) into a **backend-agnostic, real-time TTS server** that can drive **any** TTS inference engine/API (SNAC/Orpheus GGUF via llama.cpp, Piper, XTTS, Coqui, ElevenLabs-style, VITS, local WebRTC DSP pipelines, etc.), with **dynamic generation rate** control and **true real-time** streaming. Maintain the current Web UI + OpenAI-compatible surface, but make the audio pipeline modular, low-latency, and resilient. At present, the "FastAPI" is essentially bloat, as it is unable to actually perform inference (requiring a separate llama/transformers engine) except when running as a Docker container, severely limiting its incorporation into workflows. We want to change that.

## Constraints (hard)

* Local-first, no cloud dependency.
* Python 3.10–3.11 only (no 3.12).
* Support CUDA 12.4+ (driver can be newer) and CPU mode.
* Keep `/v1/audio/speech` (OpenAI-compatible) and legacy `/speak`.
* Preserve SNAC path (Orpheus via llama.cpp `/v1/completions`), but **abstract it** behind a clean adapter interface.
* Backends must be loadable/unloadable at runtime via config/API without server restart.
* Zero breaking changes for basic cURL examples.

## Performance targets (on RTX 5070 Ti 16GB)

* **TTFT** (time-to-first-audio): ≤ 200 ms for short inputs (<150 chars).
* **Sustained RT factor**: ≥ 1.5× for continuous text (≥ 1k chars) with stitching.
* **Decoder cadence**: adaptive; target **32-token** SNAC windows when stable; drop to **8–16** on barge-in/low-latency mode.
* **Jitter tolerance**: ≤ 50 ms inter-chunk drift on streaming endpoint.
* Concurrency: ≥ 4 independent streams with predictable QoS.

## High-level architecture

Introduce a **Backend Adapter Layer** + **Realtime Orchestrator** + **I/O Drivers**:

```
app.py (FastAPI)
  └─ services/
     ├─ orchestrator.py          # realtime scheduler, rate control, backpressure, barge-in
     ├─ adapters/                # pluggable backends (see adapter spec below)
     │   ├─ snac_llamacpp.py
     │   ├─ piper.py
     │   ├─ xtts.py
     │   ├─ coqui.py
     │   └─ openai_tts.py
     ├─ audio/
     │   ├─ chunker.py           # text chunking, prosody hints, punctuation-aware
     │   ├─ stitcher.py          # overlap-add, 50 ms crossfade, drift correction
     │   ├─ resample.py          # enforce 24 kHz mono pipeline
     │   └─ snac_codec.py        # SNAC encode/decode (when needed)
     ├─ config.py                # env/.env + hot-reloadable settings
     └─ metrics.py               # prometheus-style counters/histograms
static/, templates/              # keep UI, add live perf panel
```

### Adapter interface (strict)

Create `services/adapters/base.py`:

```python
from typing import AsyncIterator, Optional, Dict, Any, List
from dataclasses import dataclass

@dataclass
class TTSInput:
    text: str
    voice: str
    language: Optional[str] = None
    speed: float = 1.0
    emotion_tags: Optional[List[str]] = None
    # optional low-level knobs (temperature, top_p, penalty)
    sampling: Optional[Dict[str, Any]] = None
    # realtime hints
    target_chunk: int = 32       # desired token/audio units per callback
    low_latency: bool = False    # prefer early first audio over throughput

@dataclass
class AudioChunk:
    pcm: bytes                   # 16-bit PCM mono, 24 kHz
    duration_ms: int             # wall-clock audio duration
    is_final: bool = False       # stream end

class TTSAdapter:
    name: str
    sample_rate: int = 24000

    async def synth_stream(self, req: TTSInput) -> AsyncIterator[AudioChunk]:
        """Yield AudioChunk as soon as available. Must never block on full synthesis."""
        raise NotImplementedError()

    async def warmup(self) -> None:
        """Load weights/session, do a tiny dummy run to prime kernels/caches."""

    async def health(self) -> Dict[str, Any]:
        """Return {ready: bool, vram_mb:int, loader:str, backend:str}."""
```

Implement adapters:

* **snac\_llamacpp.py**: talks to llama.cpp `/v1/completions`, converts SNAC tokens → PCM via SNAC decoder; honors `target_chunk` and `low_latency`.
* **piper.py**: wraps Piper CLI or Python lib; chunking at sentence/phrase; stream partials if supported, else synth to memory and slice.
* **xtts.py / coqui.py / openai\_tts.py**: wrap respective APIs; normalise to PCM 24 kHz when streaming yields frames.

### Orchestrator (dynamic rate controller)

`services/orchestrator.py` implements:

* **Rate module**: adaptive chunk sizing (8/16/24/32 tokens or \~240/480/720/960 samples) based on:

  * observed **decode throughput** (tokens/s or ms/chunk),
  * **playback buffer depth** (target 200–500 ms),
  * **network/client read rate**,
  * **barge-in** (user voice/VAD signal optional; for now, treat a control flag).
* **Backpressure**: if client is slow, shrink `target_chunk` and suspend requests to backend.
* **Prefetch**: keep **1–2 chunks** ahead of the playback buffer; never synthesize huge futures.
* **Switch policy**: if adapter stalls, retry smaller chunk; if still stalling, failover to a secondary backend (configured) with a “degraded” flag.
* **Barge-in**: expose hook to immediately **pause** synthesis mid-chunk, truncate buffer, and flush.

State machine:

```
INIT → WARMUP → FILL (grow buffer to 300ms) → STEADY (keep 250–400ms)
           ↑                ↓
       DROP/RECOVER  ←  UNDERFLOW
```

### API surface (no breaking changes)

* `/v1/audio/speech` (OpenAI-compatible): takes `model`, `input`, `voice`, `speed`, returns **HTTP chunked** WAV stream or full WAV when `stream=false`.
* `/speak`: legacy wrapper.
* New:

  * `/adapters` → list active adapters + health.
  * `/config` (GET/POST) → hot-reload backend selection, default voice, chunk targets, thresholds.
  * `/metrics` → Prometheus text format.

### Config (hot-reloadable)

`.env` and runtime overrides:

```
TTS_BACKEND=snac_llamacpp        # default
BACKENDS=snac_llamacpp,piper,xtts
SNAC_URL=http://127.0.0.1:5006/v1/completions
SNAC_TARGET_CHUNK=32
SNAC_FIRST_CHUNK=12              # for TTFT
PLAYBACK_BUFFER_MS=300
BUFFER_MIN_MS=200
BUFFER_MAX_MS=500
PARALLEL_STREAMS=4
LLAMACPP_BATCH_SIZE=1024
LLAMACPP_UBATCH=512
```

## Concrete refactor plan (commit sequence)

1. **Extract adapters**: move current SNAC/llama.cpp logic out of `inference.py` into `services/adapters/snac_llamacpp.py` implementing the base interface.
2. **Introduce orchestrator**: new `services/orchestrator.py` that accepts a `TTSAdapter` and a `TTSInput`, performs adaptive scheduling, yields `AudioChunk`.
3. **Rewrite handlers** in `app.py`: `/v1/audio/speech` consumes **stream from orchestrator**, writes WAV headers once, then interleaves PCM chunks (chunked transfer).
4. **Audio stitcher**: move crossfade/overlap-add into `services/audio/stitcher.py`; expose `stitch(chunks, crossfade_ms=50)`.
5. **Pluggable registry**: `services/adapters/__init__.py` with a registry dict `{name: AdapterClass}`; read `TTS_BACKEND`, enable runtime switch via `/config`.
6. **Metrics/logging**: add `services/metrics.py` (Prometheus); instrument:

   * `tts_ttft_ms`, `tts_chunk_ms`, `tts_stream_rtf`, `tts_underflow_count`, `tts_backend_failover_total`.
7. **Web UI**: add a live perf panel (WebSocket) showing buffer depth, chunk size, RTF, current backend.
8. **Tests**: implement unit & integration tests (see Acceptance below).
9. **Docs**: update README with backend matrix and example configs.

## Smarter dynamic generation rate (algorithm)

* Start with **FIRST\_CHUNK\_TOKENS** = 8/12/16 based on latency profile config.
* Maintain target buffer depth **B** (ms). While **buffer < B**, request chunk with **size = min(32, size\*1.5)**.
* If **underflow** (buffer < MIN\_B), shrink to **size = max(8, size/2)** and set `low_latency=True`.
* If **overflow** (buffer > MAX\_B), pause requests until buffer returns to B, then reduce size slightly.
* Apply **EWMA** on observed chunk time to stabilize oscillations.
* Hard limits: 8 ≤ size ≤ 64 (tokens) for SNAC; for waveform backends, use \~100–500 ms audio frames.
* Allow **manual override** via `/config` to lock chunk size.

## Adapter specifics (minimum viable)

### snac\_llamacpp.py

* POST to `/v1/completions` with `stream:true`, `n_predict`, `cache_prompt:true`.
* Accumulate tokens; when reaching `target_chunk`, decode via SNAC to PCM (24k).
* Yield `AudioChunk(pcm=…, duration_ms=… )` ASAP.
* Respect `low_latency`: smaller first chunk; no coalescing; flush early.
* Handle EOS token → `is_final=True`.

### piper.py

* If Piper supports streaming, forward frames immediately; else synthesize to memory then slice into 100–200 ms frames and yield.

### xtts.py / coqui.py / openai\_tts.py

* Use vendor streaming APIs where available; normalize to PCM 24 kHz mono; emit incremental `AudioChunk`.

## Acceptance (must pass)

1. **API compatibility**: existing cURL examples work; `/v1/audio/speech` returns playable WAV bytes while streaming.
2. **Hot swap**: `/config` POST `{ "tts_backend":"piper" }` switches backend in-flight (new requests use it) without server restart.
3. **Realtime**: For 1k-char English text on RTX 5070 Ti, measured `tts_stream_rtf ≥ 1.5` after first 1s warmup; **TTFT ≤ 200 ms** for 120-char input at default settings.
4. **Stability**: No buffer underflow audible gaps during 5-minute narration; `tts_underflow_count==0` under default settings.
5. **Barge-in**: If `low_latency` flag is set on the request, first audio arrives ≤ 150 ms (smaller chunk), then rate ramps to steady 24–32 tokens per chunk.
6. **Unit tests**:

   * chunker splits by punctuation and preserves tags;
   * stitcher overlap-add introduces < −45 dB crossfade seam;
   * orchestrator’s EWMA converges and maintains buffer in \[200,500] ms with synthetic backends.

## Coding guidelines

* Async throughout (`async def`, `await`); no blocking disk I/O in hot path.
* Use `httpx.AsyncClient` with keep-alive for backend HTTP calls.
* WAV streaming: write RIFF header once, then stream PCM; if length unknown, use data chunk size 0xFFFFFFFF with HTTP chunked transfer (supported by most clients).
* Centralize config (`services/config.py`) with pydantic; support `.env` hot-reload (watcher).
* Structured logs (JSON) with timestamps; include `request_id`, `backend`, `chunk_size`, `buffer_ms`.

## Concrete TODOs for Codex (create/modify these)

* [ ] `services/adapters/base.py` (interface + dataclasses)
* [ ] `services/adapters/snac_llamacpp.py` (full)
* [ ] `services/adapters/piper.py` (full)
* [ ] `services/adapters/xtts.py` (skeleton with TODOs; document env vars)
* [ ] `services/adapters/openai_tts.py` (simple)
* [ ] `services/orchestrator.py` (scheduler + EWMA + backpressure)
* [ ] `services/audio/chunker.py` (punctuation/emoji/emotion-tag aware)
* [ ] `services/audio/stitcher.py` (OLA with 50 ms crossfade; drift guard)
* [ ] `services/audio/snac_codec.py` (wrap existing SNAC usage cleanly)
* [ ] `services/config.py` (pydantic settings + hot reload)
* [ ] `services/metrics.py` (Prometheus)
* [ ] `app.py` (wire endpoints to orchestrator; add `/adapters`, `/config`, `/metrics`)
* [ ] `tests/` with unit + integration (use a **FakeAdapter** that yields synthetic PCM)

## Example: wiring `/v1/audio/speech`

```python
@app.post("/v1/audio/speech")
async def audio_speech(req: SpeechRequest):
    adapter = registry.get(current_settings.tts_backend)
    await adapter.warmup()
    tts_input = TTSInput(
        text=req.input, voice=req.voice or current_settings.default_voice,
        speed=req.speed or 1.0, emotion_tags=parse_tags(req.input),
        sampling={"temperature": req.temperature, "top_p": req.top_p},
        target_chunk=current_settings.snac_target_chunk,
        low_latency=req.low_latency or False,
    )
    stream = orchestrator.stream(adapter, tts_input)
    return StreamingResponse(wav_streamer(stream, sample_rate=adapter.sample_rate),
                             media_type="audio/wav")
```

## Bench script (dev utility)

Add `scripts/bench.py` to run fixed prompts against all adapters, print TTFT, RTF, avg chunk size, underflows.

---

**Deliverables:** a PR touching files above, passing acceptance tests, with `README.md` updated (backend matrix, config, perf tips). Keep changes cohesive, no dead code, and leave the original Orpheus path working through the SNAC adapter.

If anything is ambiguous, decide in favor of **lower latency**, **clean interfaces**, and **hot-swappable backends**.

