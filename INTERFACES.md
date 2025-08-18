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
- **Purpose:** Expose runtime metrics for operators.
- **Shape:**
  - **Request/Input:** `GET /stats`
  - **Response/Output:** `{uptime_ms, active_requests, adapters}`
- **Idempotency/Retry:** read-only; safe to retry.
- **Stability:** experimental
- **Versioning:** none
- **Auth/Access:** operator only
- **Observability:** emits `stats_requested` event
- **Failure Modes:** `503` when orchestrator not initialized
- **Owner:** repo owner
- **Code:** `Orpheus-FastAPI/app.py`
- **Change Log:**
  - 2025-09-01: documented endpoint

### Surface: config-endpoint
- **Type:** API
- **Purpose:** Update active adapter or voice.
- **Shape:**
  - **Request/Input:** `POST /config` with `{adapter?, voice?}`
  - **Response/Output:** `{adapter, voice}`
- **Idempotency/Retry:** repeated calls override current state
- **Stability:** experimental
- **Versioning:** none
- **Auth/Access:** operator only
- **Observability:** emits `config_update` event
- **Failure Modes:** `404` for unknown adapter
- **Owner:** repo owner
- **Code:** `Orpheus-FastAPI/app.py`
- **Change Log:**
  - 2025-09-01: documented endpoint

### Surface: admin-endpoint
- **Type:** API
- **Purpose:** Serve administration UI and actions.
- **Shape:**
  - **Request/Input:** `GET /admin` (HTML), `POST /admin` actions
  - **Response/Output:** HTML or `{status}`
- **Idempotency/Retry:** `GET` is idempotent; actions may not be
- **Stability:** experimental
- **Versioning:** none
- **Auth/Access:** operator only
- **Observability:** access logged as `admin_access`
- **Failure Modes:** `503` if service not ready
- **Owner:** repo owner
- **Code:** `Orpheus-FastAPI/app.py`
- **Change Log:**
  - 2025-09-01: documented endpoint

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
