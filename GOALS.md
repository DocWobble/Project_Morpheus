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
