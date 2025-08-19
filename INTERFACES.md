# INTERFACES.md

> Define only the **surfaces** other code or operators depend on.  
> Keep shapes tight; no examples; no prose tutorials.

## Rules

- Document a surface the moment its **shape or stability** changes.
- Prefer a single canonical entry per surface; link to code location.
- Surfaces include: APIs, CLIs, message topics, file formats, configs, scheduled jobs.

---

## Surface Entry Template

### Surface: <name>
- **Type:** API | CLI | File | Event | Job | Library
- **Purpose:** <what this surface does in one line>
- **Shape:** 
  - **Request/Input:** <fields and required invariants>
  - **Response/Output:** <fields and invariants; error envelope if any>
- **Idempotency/Retry:** <keys, replay tokens, or statement of non-idempotency>
- **Stability:** experimental | beta | stable | deprecated
- **Versioning:** <semver policy; header/param/feature flag>
- **Auth/Access:** <who/what can call it; tokens/roles if applicable>
- **Observability:** <events/metrics emitted and where>
- **Failure Modes:** <timeouts, partial results, backpressure story>
- **Owner:** repo owner
- **Code:** `<path/to/implementation>`
- **Change Log:** <brief bullet list of meaningful changes with commit/PR ids>

### Surface: cli-login-helpers
- **Type:** Library
- **Purpose:** Programmatic login/logout operations for Codex.
- **Shape:**
  - **Request/Input:**
    - `run_login_with_chatgpt(overrides) -> Result<()>`
    - `run_login_with_api_key(overrides, api_key) -> Result<()>`
    - `run_login_status(overrides) -> Result<LoginStatus>`
    - `run_logout(overrides) -> Result<LogoutStatus>`
  - **Response/Output:** status enums or `()`; errors via `anyhow::Error`.
- **Idempotency/Retry:** login/logout mutate credentials; status is read-only.
- **Stability:** experimental
- **Versioning:** semver via `codex-cli`
- **Auth/Access:** filesystem access to `CODEX_HOME`
- **Observability:** messages printed to stderr
- **Failure Modes:** config parse errors, filesystem I/O failures
- **Owner:** repo owner
- **Code:** `codex-rs/cli/src/login.rs`
- **Change Log:**
  - 2025-08-19: return `Result` from helpers (#PR)

### Surface: stats-endpoint
- **Type:** API
- **Purpose:** Expose orchestrator timeline and transcripts for live monitoring.
- **Shape:**
  - **Request/Input:** `GET /stats`
  - **Response/Output:** `{ "timeline": [<timeline-events>], "transcripts": [ {timestamp,text} ] }` (non-streaming JSON)
- **Idempotency/Retry:** read-only; safe to retry.
- **Stability:** experimental
- **Versioning:** none
- **Auth/Access:** operator only
- **Observability:** timeline events and transcripts appended in memory
- **Failure Modes:** `503` when orchestrator not initialized
- **Owner:** repo owner
- **Code:** `Morpheus_Client/server.py`
- **Change Log:**
  - 2025-09-21: updated shape to timeline JSON
  - 2025-09-27: added transcript history to response

### Surface: config-endpoint
- **Type:** API
- **Purpose:** Read and update configuration.
- **Shape:**
  - **Request/Input:**
    - `GET /config`
    - `POST /config` with `{adapter?, voice?, source?, source_config?, ORPHEUS_*?}`
  - **Response/Output:**
    - `GET` → `{...}` current config
    - `POST` → `{message, adapter?, voice?, source?}`
- **Idempotency/Retry:** `GET` is idempotent; `POST` overwrites provided keys
- **Stability:** experimental
- **Versioning:** none
- **Auth/Access:** operator only
- **Observability:** emits `config_update` event
- **Failure Modes:** `404` for unknown adapter or source
- **Owner:** repo owner
- **Code:** `Morpheus_Client/server.py`
- **Change Log:**
  - 2025-09-01: documented endpoint
  - 2025-09-14: added text source configuration
  - 2025-10-09: added GET and persistence via `.env`
  - 2025-10-24: allow `source_config` for constructor options
  - 2025-08-19: mirror config to `~/.morpheus/config` and load it before `.env`
  - 2025-10-30: validate and persist `ORPHEUS_TEMPERATURE`, `ORPHEUS_TOP_P`, `ORPHEUS_MAX_TOKENS`

### Surface: admin-endpoint
- **Type:** API
- **Purpose:** Serve administration UI and actions.
- **Shape:**
  - **Request/Input:** `GET /admin` (HTML)
  - **Response/Output:** HTML (non-streaming)
- **Idempotency/Retry:** `GET` is idempotent; actions may not be
- **Stability:** experimental
- **Versioning:** none
- **Auth/Access:** operator only
- **Observability:** access logged as `admin_access`
- **Failure Modes:** `503` if service not ready
- **Owner:** repo owner
- **Code:** `Morpheus_Client/server.py`
- **Change Log:**
  - 2025-09-01: documented endpoint

### Surface: speech-endpoint
- **Type:** API
- **Purpose:** Stream synthesized audio.
- **Shape:**
  - **Request/Input:** `POST /v1/audio/speech` with `{input, voice?}`
  - **Response/Output:** WAV audio streamed via chunked transfer (RIFF header then PCM frames)
- **Idempotency/Retry:** non-idempotent; repeated calls re-synthesize audio
- **Stability:** experimental
- **Versioning:** none
- **Auth/Access:** public
- **Observability:** timeline events emitted per chunk
- **Failure Modes:** `400` on validation error, `503` if orchestrator not ready
- **Owner:** repo owner
- **Code:** `Morpheus_Client/server.py`
- **Change Log:**
  - 2025-09-21: documented endpoint

### Surface: client-voices-endpoint
- **Type:** API
- **Purpose:** List available synthesis voices.
- **Shape:**
  - **Request/Input:** `GET /v1/audio/voices`
  - **Response/Output:** `{status, voices}`
- **Idempotency/Retry:** read-only; safe to retry.
- **Stability:** experimental
- **Versioning:** none
- **Auth/Access:** public
- **Observability:** none
- **Failure Modes:** `404` when no voices available
- **Owner:** repo owner
- **Code:** `Morpheus_Client/server.py`
- **Change Log:**
  - 2025-08-18: documented endpoint

### Surface: client-adapters-endpoint
- **Type:** API
- **Purpose:** Expose capability descriptors for registered adapters.
- **Shape:**
  - **Request/Input:** `GET /adapters`
  - **Response/Output:** `{adapter_name: descriptor}`
- **Idempotency/Retry:** read-only; safe to retry.
- **Stability:** experimental
- **Versioning:** none
- **Auth/Access:** public
- **Observability:** none
- **Failure Modes:** none
- **Owner:** repo owner
- **Code:** `Morpheus_Client/server.py`
- **Change Log:**
  - 2025-08-18: documented endpoint

### Surface: client-sources-endpoint
- **Type:** API
- **Purpose:** Expose capability descriptors for text sources.
- **Shape:**
  - **Request/Input:** `GET /sources`
  - **Response/Output:** `{source_name: descriptor}`
- **Idempotency/Retry:** read-only; safe to retry.
- **Stability:** experimental
- **Versioning:** none
- **Auth/Access:** public
- **Observability:** none
- **Failure Modes:** none
- **Owner:** repo owner
- **Code:** `Morpheus_Client/server.py`
- **Change Log:**
  - 2025-09-14: documented endpoint

### Surface: client-admin-static
- **Type:** Static
- **Purpose:** Serve admin interface assets.
- **Shape:**
  - **Request/Input:** `GET /admin/{asset}`
  - **Response/Output:** HTML/CSS/JS
- **Idempotency/Retry:** read-only; safe to retry.
- **Stability:** experimental
- **Versioning:** none
- **Auth/Access:** operator only
- **Observability:** none
- **Failure Modes:** `404` for missing asset
- **Owner:** repo owner
- **Code:** `Morpheus_Client/server.py`
- **Change Log:**
  - 2025-09-02: mounted admin static assets

### Surface: timeline-events
- **Type:** Event
- **Purpose:** Structured telemetry of orchestrator stages.
- **Shape:**
  - **Event:** `{stage: str, duration_ms: float, result: str}`
- **Idempotency/Retry:** append-only; no retry.
- **Stability:** experimental
- **Versioning:** none
- **Auth/Access:** internal
- **Observability:** persisted to `SCENES/_artifacts/timeline.json`
- **Failure Modes:** events lost if process crashes
- **Owner:** repo owner
- **Code:** `Morpheus_Client/orchestrator/core.py`
- **Change Log:**
  - 2025-09-08: initial schema

