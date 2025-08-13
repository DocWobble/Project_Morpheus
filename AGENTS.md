

# End-State Phenotype (what it should *feel* like)

* **Live voice, not files.** You type/speak → it **starts speaking while it’s thinking**, and you can **barge-in** at any time; playback pauses instantly and resumes coherently.
* **Backend-agnostic voice.** You can switch TTS engines on the fly (SNAC/Orpheus, ouleTTS, XTTS, Piper, Eleven-ish, etc.). The *voice persona* persists across the swap; at worst the timbre shifts, never the timing.
* **Duplex loop.** Conversational core and coding core can talk over the voice without blocking each other; speech is just another stream on the bus.
* **Graceful degradation.** If GPU is busy or a backend stalls, it **keeps talking** with simpler synthesis (or smaller chunks) rather than freezing. No clicks, no gaps—just a subtle quality trade.
* **Truthful surface.** The UI shows a **time-aligned timeline** of: input chunks, token windows, audio frames, barge-ins, backend swaps, and tool actions. What you hear matches what the timeline shows.

---

# Behavioral Invariants (morphology, not metrics)

Think of these as the “duckbill” of the system—non-negotiable shapes the stack must exhibit regardless of backend.

1. **Stream-first, file-never (hot path).** No disk writes in the synthesis path; audio is produced as a **monotonic stream of PCM frames** with a single WAV header (or WS frames).
2. **Rolling context, bounded working set.** Inference uses a **sliding window** of the minimal past it needs; old phoneme/audio state is spillable to CPU/RAM. VRAM never scales with total utterance length.
3. **Backpressure aware.** Producers honor a **playback buffer** contract: keep it within a soft band (buffer is an integrator; controller nudges chunk size and pacing to hold it). No underflows; no unbounded growth.
4. **Seamless interruptions.** A **barge-in signal** can arrive at any time; the orchestrator must cut synthesis at the next frame boundary, **flush** the buffer, and re-seed context without artifacts.
5. **Late binding of voice.** “Voice” is a **schema**, not an index: `{timbre, prosody, accent, emotion-priors, pace}`. Backends project that schema into their own knobs; the request stays the same.
6. **Idempotent retries.** If a chunk decode fails, replaying the same token/window yields **byte-identical** PCM (determinism under fixed seed) so we can resume mid-stream.
7. **Hot-swappable adapters.** Adapter swap is a **state machine transition**, not a restart: capture current envelope (RMS/pitch/speed), crossfade **≤ one frame** overlap, and continue.
8. **Observability ≥ UX.** Every emitted frame has provenance: `{adapter, chunk_id, window_tokens, render_ms}`; the UI can **replay** any session deterministically.

---

# Synchrony Contracts (how layers coordinate)

* **Ingress → Orchestrator:** `{text or tokens, voice schema, mode:{low_latency|steady}, hints:{target_chunk, cadence}}`
* **Orchestrator → Adapter:** **pull** contract: “give me next AudioChunk when ready”; adapter may push early partials.
* **Adapter → Orchestrator:** `AudioChunk{pcm, duration_ms, markers?, eos?}`; **never blocks** while waiting for full utterance.
* **Orchestrator → Stitcher:** `[(chunk_i, overlap_ms)]` → returns a continuous stream with overlap-add and **drift guard** (timebase authority is playback).
* **Control plane:** `/config` can change adapter, voice schema, or mode mid-request; changes take effect on **next chunk boundary**.

---

# Adaptive Rate Controller (shape, not numbers)

* Treat the playback buffer as the **controlled variable**; keep it in a **comfort band** (e.g., “one breath” deep) without hardcoding ms.
* Start with a **small first window** (low-latency morphology), then **expand** chunk size toward a stable maximum the backend can sustain.
* If buffer shrinks, **halve** the next request size and set `low_latency=True`.
* If buffer grows beyond comfort, **skip one request** (let playback catch up) and step chunk size down one notch.
* Use **EWMA** on observed chunk render time; don’t chase noise.
* Chunk size ladder is discrete: `{8, 12, 16, 24, 32, 48, 64}` tokens or equivalent ms for non-token engines.

---

# Adapter Capability Descriptor (self-description, not hardcoding)

Each adapter exposes:

```json
{
  "name": "snac_llamacpp",
  "streaming": true,
  "unit": "tokens|ms",
  "granularity": [8,12,16,24,32,48,64],
  "voices": ["..."] or "dynamic",
  "supports_barge_in": true,
  "supports_seed": true,
  "stateful_context": "rolling|minimal|none"
}
```

The orchestrator **negotiates** target chunking and barge-in semantics from this, so new engines slot in without changing control logic.

---

# Scenario Probes (open-ended tests that force emergence)

Instead of brittle thresholds, give the agent **scenes** it must pass. Each scene asserts **shapes** in the timeline/PCM, not single numbers.

1. **Breathing Room.** Short utterances; confirm *first-audio begins before silence fully decays* and no file appears on disk.
2. **Long Read.** 5-minute narration; confirm **no underflows**, chunk sizes converge, and adapter returns stable cadence after a minute.
3. **Mid-Stream Swap.** Switch adapters while speaking; confirm single-frame crossfade, same words continue, voice schema preserved.
4. **Barge-In.** Interrupt repeatedly at random points; confirm hard stop at frame boundary, buffer flush, and fast re-seed.
5. **Throttle & Recover.** Inject GPU/HTTP slowdown; controller shrinks chunks, then expands when pressure releases—no audible hiccups.
6. **Persona Script.** Apply a JSON voice persona (à la ouleTTS) to three backends; confirm perceptual similarity in **prosody envelope** (not identical timbre).
7. **Cold Start.** First request after boot; confirm warm-up path compiles kernels and preallocates buffers; later requests skip warm-up.

Each scene produces a **timeline artifact** (JSON) and a **WAV**; a human can audition, and the CI can check coarse properties (continuous RMS, bounded zero-runs, monotonic timestamps).

---

# Deliverables for the coding agents (what to build)

1. **Orchestrator (new)**

   * Pull-based streaming core with adaptive chunk ladder, barge-in, and backpressure.
   * Zero-copy PCM ring buffer; playback is the clock.

2. **Adapter Registry + Capabilities**

   * `base.TTSAdapter` + `describe()`; adapters for `snac_llamacpp`, `piper`, `xtts`, `ouleTTS`, `openai_speech`.
   * Voice schema mapper per adapter (name → backend params or JSON persona).

3. **Unified Streaming Surface**

   * HTTP chunked WAV **and** WebSocket PCM frames; one RIFF header, then frames; no `FileResponse` ever in hot path.

4. **Stitcher**

   * Overlap-add with drift guard; optional noise-floor dither; emits **markers** (word/phoneme boundaries if provided).

5. **Timeline & Replay**

   * Append-only JSON log of chunks/events; deterministic **replay** runner that regenerates audio from the log.

6. **UI Synchrony Panel**

   * Live strip chart: buffer depth, chunk size, adapter, events; click to audition from any marker.

7. **Scenario Harness**

   * `scenes/` library implementing the probes above; single command runs all scenes across adapters, saves artifacts.

8. **Config & Hot-Swap**

   * `/config` endpoint that flips adapter/voice/mode at next chunk boundary; `/adapters` for capability introspection.

9. **Safety & Isolation**

   * No network egress except declared backends; adapters run in their own process if they link heavy runtimes (optional).

10. **Docs as Morphology**

* README section “Phenotype”: diagrams of streams, buffers, and state transitions; troubleshooting by **shape** (e.g., “sawtooth buffer → chunk too big or backend jitter”).

---

# How this prevents gremlins

* You’re constraining **interaction geometry**, not one-off numbers. Any backend that can maintain those shapes will behave correctly.
* Adaptive control + scenario probes **invite emergence** (the controller finds the stable regime on your hardware) while keeping UX invariants intact.
* Replayable timelines make bugs diagnosable: when something sounds wrong, you inspect the **shape** of the stream and reproduce it exactly.


