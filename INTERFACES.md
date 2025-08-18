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

