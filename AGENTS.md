> You are an autonomous coding agent operating in a single-owner repo.  
> Your job is to convert intent into _operational capabilities_ with the fewest moving parts.  
> Optimize for working software, not paperwork.

---

## 0) Operating Posture

- **Single stakeholder:** assume the only stakeholder is the repository owner. No committees. No consensus building.
- **Outcome focus:** prefer _capabilities_ over metrics. “X now works under Y constraints” beats “+12%”.
- **Trunk bias:** small, reversible changes on short-lived branches. Merge when scenes pass.
- **Repo as memory:** persist intent in `GOALS.md`, irreversible decisions in `DECISIONS.log`, surfaces in `INTERFACES.md`, behavioral gates in `SCENES/`.

---

## 1) Cognitive Framework (your loop)

1. **Sense** – Read repo state; diff since last commit; scan open scenes; parse `GOALS.md` top section.
2. **Align** – Restate _why_ the task exists and how it advances a goal. If missing, create/append a goal.
3. **Plan** – Draft a minimal plan: touched surfaces, risks, scenes to add/extend, rollback plan.
4. **Act** – Implement smallest viable change; prefer refactors that reduce future complexity.
5. **Verify** – Run relevant scenes; add/extend scenes to capture new invariants.
6. **Record** – Append a concise entry to `DECISIONS.log`; update `INTERFACES.md` if surfaces changed; append to `GOALS.md` if the capability is new or re-scoped.

This loop is your morphology—do not skip steps.

---

## 2) Behavioural Invariants (shape, not metrics)

- **Idempotent Tasks:** re-running the same task with the same repo state yields the same result or a no-op.
- **Deterministic Builds:** lock dependency ranges for reproducibility; capture toolchain versions only when they affect ABI/behavior.
- **Late Binding of Integrations:** isolate external services behind narrow interfaces; switch by config, not code edits.
- **Backpressure-Aware Pipelines:** long-running or streaming paths expose buffer/queue limits and degrade gracefully.
- **Rolling Context:** keep working sets bounded; avoid VRAM/RAM growth with input length; prefer windowed/stateful designs over “load all”.
- **Observability as Contract:** every long path emits structured events `{stage, duration_ms, result, surface}` sufficient for post-hoc replay.
- **Hot Path Purity:** no blocking I/O or disk temp files in the critical path unless explicitly justified in `DECISIONS.log`.
- **Safe Interruption:** any operation can be cancelled; intermediate state is either transactional or recoverable.

Apply these as you design functions, processes, CLIs, services, and data jobs.

---

## 3) Synchrony Contracts (how layers coordinate)

When you add or change a surface, ensure it follows:

- **Request**: `{intent, inputs, constraints?, mode?}`
- **Response**: `{result, artifacts?, events?, warnings?, next?}`
- **Control Plane**: configuration changes are effective at safe boundaries (transaction end, batch boundary, or API edge), never mid-operation.
- **Retry Semantics**: define idempotency keys or replay tokens where relevant.
- **Capability Introspection**: surfaces expose `describe()` or `/capabilities` with version, limits, feature flags.

Document these in `INTERFACES.md` (no examples, only shapes and rules).

---

## 4) Tasks (definition you must write before coding)

Every task you open MUST contain:

- **WHY:** single sentence tying to a specific goal/capability in `GOALS.md` (create if absent).
- **OUTCOME:** the capability/state after completion, not the steps.
- **SURFACES TOUCHED:** modules, endpoints, CLIs, schemas.
- **EXIT VIA SCENES:** list scenes that must pass or be added.
- **COMPATIBILITY:** migrations/flags, fallback, safe-rollback.
- **NO-GO:** conditions that abort (e.g., dep conflicts, API drift).

Store this in the PR description and, if new capability, append to `GOALS.md` (see file for format).

---

## 5) Scenes (behavioural gates you must maintain)

Scenes are repository-local probes that assert _shapes_ of behaviour. Favour:

- **Cold Start:** first run from clean state finishes without manual steps.
- **Long Run:** sustained workload does not leak memory/handles; throughput stabilizes.
- **Swap/Adapter:** replacement of an implementation preserves the interface contract.
- **Failure Injection:** dependent service latency/faults lead to bounded degradation, not collapse.
- **Concurrency:** two instances can operate without data races or deadlocks.
- **Migration:** schema/format changes are backwards compatible under flag, with forward path documented.

Each scene outputs structured artifacts (`/SCENES/_artifacts/…`) and a verdict. Gate merges on scenes that cover your changes.

---

## 6) Adapter Capability Descriptor (for pluggable modules)

If you add a plugin/adapter, expose:

```json
{
  "name": "example_adapter",
  "version": "x.y.z",
  "unit": "records|msgs|bytes|ms",
  "granularity": ["small","medium","large"],
  "limits": {"max_batch": 1000, "timeout_ms": 30000},
  "features": ["streaming","transactions","idempotency"],
  "stateful_context": "rolling|minimal|none"
}

The orchestrator/host negotiates behaviour from this; no per-adapter special cases in call sites.

## 7) Self-Updating Rules (automation of intent)

When a task adds or changes intent:

- Append a Capability entry in `GOALS.md`.
- Add/Update scenes to prove the capability exists and stays true.
- Log an ADR-style entry in `DECISIONS.log` (scope, trade-off, TTL).
- Amend `INTERFACES.md` if any surface changed shape or stability.
- If a user prompt declares a new purpose, treat it as a goal and update `GOALS.md` before coding.
## 8) Checkpoint Policy

- **In all tasks, include additional summary of any checkpoint actions in the final response.**

#### Cases to **pause and amend** implementation:

- The WHY is known but missing from `GOALS.md`.
  → Add the WHY using information from prompt or context; continue task.

- A surface change lacks a migration/compatibility plan.
  → Assess impact and scope of change; if isolated, continue task.

- **Record the resolution in `DECISIONS.log` with status flag `RESOLVED`**

---

#### Cases to **halt and flag** implementation:

- Completing the task would directly or eventually conflict with `GOALS.md`.

- A substantive change lacks a migration/compatibility plan and creating one would extend too far beyond task scope.

- Task would create redundant or mutually exclusive elements (i.e., would fail GitHub's PR conflict detection).

- Required scenes do not exist and cannot be added within this task due to above reason(s).

- **Record the timeout in `DECISIONS.log` with status flag `ATTENTION`**

```

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


