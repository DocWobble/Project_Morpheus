# GOALS.md

> This file is the intent ledger. It is **append-only** except for status changes.  
> Entries are short and operational. No roadmaps, no OKRs.

## How to use this file (Agent)

- When a prompt implies a new purpose or constraint, **add a capability** entry first.
- When you complete a task that creates or retires a capability, **update its status**.
- Keep language generic and implementation-agnostic.

---

## Capability Entry Format (copy/paste)

### Capability: <short name>

- **Purpose:** <why this exists in the product; 1–2 lines>
- **Scope:** <surfaces affected (modules/apis/clis/data)>
- **Shape:** <behavioural invariants asserted by scenes; no numbers>
- **Compatibility:** <flags, migrations, fallbacks>
- **Status:** planned | active | deprecated | removed
- **Owner:** single stakeholder (repo owner)
- **Linked Scenes:** <ids or paths>
- **Linked Decisions:** <DECISIONS.log ids>
- **Notes:** <constraints, risks, open questions>

---

## Non-Goals

- Features that add complexity without increasing operational capability.
- Telemetry or metrics work without a user-facing or operability payoff.

---

## Current Capabilities

_(Append new capabilities below using the format above. Keep the list curated; collapse removed items to a brief tombstone if noisy.)_

### Capability: streaming-telemetry

- **Purpose:** Expose orchestrator runtime stages for live monitoring.
- **Scope:** `Morpheus_Client/orchestrator`, `/stats` API, timeline artifacts.
- **Shape:** `{stage, duration_ms, result}` events appended; `/stats` returns current timeline; artifacts saved to `SCENES/_artifacts`.
- **Compatibility:** additive; resets on process restart.
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:** `tests/test_scenes.py::test_breathing_room`
- **Linked Decisions:** orchestrator-timeline
- **Notes:** timeline growth is unbounded during run.

### Capability: graceful-missing-sandbox

- **Purpose:** Ensure the CLI reports a clear error when the `codex-linux-sandbox` binary is absent.
- **Scope:** `codex-rs/cli` Landlock sandbox execution path.
- **Shape:** Attempting Landlock without the binary yields a descriptive failure instead of a panic.
- **Compatibility:** No flags or migrations; failure surfaces as an error.
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:** `codex-rs/cli/src/debug_sandbox.rs::missing_linux_sandbox_binary_returns_error`
- **Linked Decisions:** [2025-08-17] missing-sandbox-error
- **Notes:** n/a

### Capability: result-based-login

- **Purpose:** Allow CLI login helpers to return structured results for better control and testing.
- **Scope:** `codex-rs/cli` login module and main entrypoint.
- **Shape:** login operations yield `Result`/status enums; caller decides process exit.
- **Compatibility:** no flags; CLI output unchanged.
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:** `codex-rs/cli/src/login.rs` tests
- **Linked Decisions:** [2025-08-19] login-result-handling
- **Notes:** n/a

### Capability: cli-path-deduplication

- **Purpose:** Prevent the Codex CLI from duplicating directories when updating `PATH`.
- **Scope:** `codex-cli` startup environment handling.
- **Shape:** Repeated CLI invocations do not accumulate duplicate `PATH` segments.
- **Compatibility:** no flags; existing environment variables remain unchanged.
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:** `codex-cli/test/path.test.js`
- **Linked Decisions:** [2025-08-29] cli-path-dedup
- **Notes:** n/a
### Capability: cli-exit-code-centralization

- **Purpose:** enable consistent exit code handling across CLI subcommands.
- **Scope:** `codex-rs/cli`, `codex-rs/arg0`.
- **Shape:** each subcommand returns `ExitCode`; `main` terminates once with this code.
- **Compatibility:** no flags; preserves existing behavior.
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:** `codex-rs/cli/tests/login_status.rs`, `codex-rs/cli/tests/proto.rs`
- **Linked Decisions:** [2025-08-30] cli-exitcode-refactor
- **Notes:** facilitates test assertions on exit codes

### Capability: standalone-orchestrator

- **Purpose:** Provide a self-contained orchestrator service that streams audio via the unified client server.
- **Scope:** `Morpheus_Client/server.py`, adapter registry.
- **Shape:** single ASGI service coordinates adapters and exposes `/v1/audio/speech`, `/config`, `/stats`, and `/admin`.
- **Compatibility:** configured through `.env` and `/config`; no migrations yet.
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:** TBD
- **Linked Decisions:** [2025-09-01] single-service-architecture
- **Notes:** n/a

### Capability: admin-interface

- **Purpose:** Offer operator-facing endpoints and UI for runtime control and observation.
- **Scope:** `/admin`, `/stats`, `/config`, config templates.
- **Shape:** ASGI endpoints expose status and allow configuration updates.
- **Compatibility:** auth TBD; persists changes to `.env`.
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:** `tests/test_text_sources.py::test_config_round_trip_persistence`
- **Linked Decisions:** [2025-09-01] single-service-architecture
- **Notes:** n/a

### Capability: direct-inference-integration

- **Purpose:** Connect directly to local inference backends without a separate service layer.
- **Scope:** orchestrator adapters, config entries.
- **Shape:** orchestrator calls inference libraries in-process with fallback to HTTP adapters.
- **Compatibility:** selectable via `.env` or `/config`.
- **Status:** planned
- **Owner:** repo owner
- **Linked Scenes:** TBD
- **Linked Decisions:** [2025-09-01] single-service-architecture
- **Notes:** n/a

### Capability: shared-config-module

- **Purpose:** Deduplicate environment file utilities across services.
- **Scope:** `Morpheus_Client.config`, `main.py`, `Morpheus_Client/server.py`.
- **Shape:** All components load and persist configuration through a single module.
- **Compatibility:** uses existing `.env` format; no migrations.
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:** TBD
- **Linked Decisions:** [2025-09-02] central-config-module
- **Notes:** n/a

### Capability: morpheus-client-introspection
- **Purpose:** Allow clients to discover available voices and adapter capabilities.
- **Scope:** `Morpheus_Client/server.py`, `INTERFACES.md`
- **Shape:** `GET /v1/audio/voices` → `{status, voices}`; `GET /adapters` → `{adapter_name: descriptor}`
- **Compatibility:** read-only; no flags
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:** n/a
- **Linked Decisions:** morpheus-client-endpoints
- **Notes:** none

### Capability: unified-dependency-management

- **Purpose:** Provide a single pinned dependency file with hardware guidance.
- **Scope:** requirements.txt, setup scripts, README.
- **Shape:** Installing on any hardware uses the same base file; GPU/CPU differences are documented.
- **Compatibility:** GPU extras installed manually; no migrations.
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:** TBD
- **Linked Decisions:** [2025-09-06] consolidate-requirements
- **Notes:** UI build prerequisites documented.
                                                           
### Capability: pluggable-text-sources

- **Purpose:** Consume text from interchangeable sources like WebSocket feeds or CLI pipes.
- **Scope:** `text_sources/*`, `Morpheus_Client/server.py`, `/config` endpoint.
- **Shape:** sources implement `TextSource` protocol and can be hot-swapped via config.
- **Compatibility:** selectable via `/config`; no migrations.
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:**
  - `tests/test_text_sources.py::test_cli_pipe_feeds_orchestrator`
  - `tests/test_text_sources.py::test_websocket_feeds_orchestrator`
- **Linked Decisions:** [2025-09-14] text-source-adapters
- **Notes:** initial adapters for WebSocket, HTTP polling and CLI pipe.


### Capability: auto-start-config

- **Purpose:** Simplify launching with a single script that persists user preferences.
- **Scope:** `scripts/start.py`, start scripts, `README.md`.
- **Shape:** `scripts/start.py` ensures `.env` exists, loads overrides from `~/.morpheus/config`, launches the server, and opens `/admin` in the browser.
- **Compatibility:** additive; existing `.env` remains; user config overrides via `~/.morpheus/config`.
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:** TBD
- **Linked Decisions:** [2025-09-19] start-entrypoint
- **Notes:** none

### Capability: orpheus-cpp-startup-check

- **Purpose:** Fail fast when the local C++ bindings are missing.
- **Scope:** `scripts/start.py`, `requirements.txt`, `README.md`.
- **Shape:** Startup aborts with a descriptive error if `orpheus_cpp` cannot be imported.
- **Compatibility:** additive; service does not launch without the binding.
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:** `tests/test_start_requires_orpheus_cpp.py`
- **Linked Decisions:** [2025-09-30] orpheus-cpp-required
- **Notes:** build step may take several minutes

### Capability: transcript-history

- **Purpose:** Retain utterance text for replay and monitoring.
- **Scope:** `Morpheus_Client/orchestrator`, `/stats` API, `SCENES/_artifacts`.
- **Shape:** `{timestamp,text}` entries appended per utterance; `/stats` exposes transcript list; transcripts persisted to `SCENES/_artifacts/transcripts.json`.
- **Compatibility:** additive; resets on process restart.
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:** `tests/test_stats_endpoint.py::test_stats_endpoint_exposes_timeline`, `tests/test_scenes.py::test_breathing_room`
- **Linked Decisions:** [2025-10-30] orchestrator-transcripts
- **Notes:** transcripts list grows without bound

### Capability: user-config-precedence

- **Purpose:** Allow persistent user configuration to override repo defaults.
- **Scope:** `Morpheus_Client/config.py`, `scripts/start.py`, `.env.example`.
- **Shape:** Values from `~/.morpheus/config` override `.env`; missing keys fall back to repository defaults.
- **Compatibility:** falls back to `.env` when user config is absent.
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:** `tests/test_text_sources.py`
- **Linked Decisions:** [2025-08-19] user-config-precedence
- **Notes:** home directory config created on save

### Capability: admin-voices-runtime

- **Purpose:** Admin UI loads available voices and languages at runtime from the API.
- **Scope:** `Morpheus_Client/admin/index.html`, `Morpheus_Client/server.py`
- **Shape:** `/v1/audio/voices` returns voice-language mapping; admin page fetches and renders dynamically.
- **Compatibility:** additive to existing voice list API; static `/admin` assets remain unchanged by backend config.
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:** `tests/test_admin_dynamic_voices.py::test_admin_voices_loaded_via_api`
- **Linked Decisions:** [2025-08-19] admin-voices-runtime
- **Notes:** initial load depends on voices endpoint availability

### Capability: tunable-inference-params

- **Purpose:** Allow operators to adjust sampling parameters without restart.
- **Scope:** `/config` endpoint, inference module, admin UI form.
- **Shape:** Posting `ORPHEUS_TEMPERATURE`, `ORPHEUS_TOP_P`, or `ORPHEUS_MAX_TOKENS` updates runtime behaviour and persists to `.env`.
- **Compatibility:** falls back to defaults when unspecified.
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:** `tests/test_config_generation_params.py::test_generation_param_round_trip`
- **Linked Decisions:** [2025-10-30] tunable-inference-params
- **Notes:** none

### Capability: centralized-docs

- **Purpose:** Maintain a single top-level README and requirements file for clearer setup.
- **Scope:** `README.md`, `requirements.txt`, repository docs.
- **Shape:** Only one `README.md` and `requirements.txt` exist at the repository root; subdirectory variants are archived.
- **Compatibility:** n/a
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:** n/a
- **Linked Decisions:** consolidate-readmes
- **Notes:** documents text-stream output and client/UI startup.
- **Notes:** updated 2025-08-24 to describe WAV streaming endpoints.

### Capability: idempotent-miniforge-setup

- **Purpose:** Avoid reinstalling Miniforge when running the environment setup multiple times.
- **Scope:** `scripts/one_click.py`.
- **Shape:** Presence of `miniforge3` directory or `conda` binary results in a no-op.
- **Compatibility:** no flags; existing installations remain untouched.
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:** tests/test_one_click.py::test_miniforge_detection_and_skip
- **Linked Decisions:** [2025-08-24] miniforge-idempotent
- **Notes:** re-evaluate if update-through-installer is required


### Capability: gpu-aware-one-click

- **Purpose:** Automatically install GPU-optimized dependencies when hardware is present.
- **Scope:** `scripts/one_click.py`, `requirements.txt`.
- **Shape:** Setup detects `nvidia-smi` or `rocm-smi` and installs matching Torch, `llama-cpp-python`, and GPU extras; falls back to CPU wheels otherwise.
- **Compatibility:** CPU-only systems continue using standard packages.
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:**
  - `tests/test_one_click.py::test_detect_gpu_cuda`
  - `tests/test_one_click.py::test_install_torch_cuda`
- **Linked Decisions:** [2025-09-20] one-click-gpu-detection
- **Notes:** `bitsandbytes` and `flash-attn` installs are best effort.


### Capability: auto-venv-setup

- **Purpose:** Ensure one-click script initializes and uses a dedicated virtual environment.
- **Scope:** `scripts/one_click.py`, `tests/test_one_click.py`.
- **Shape:** `.venv` is created if missing and dependency installation uses its Python executable.
- **Compatibility:** additive; existing `.venv` remains untouched.
- **Status:** active
- **Owner:** repo owner
- **Linked Scenes:**
  - `tests/test_one_click.py::test_ensure_venv_creates_and_returns_python`
  - `tests/test_one_click.py::test_install_requirements_uses_given_python`
- **Linked Decisions:** [2025-08-24] one-click-venv
- **Notes:** remind users to activate the virtual environment before starting the server

