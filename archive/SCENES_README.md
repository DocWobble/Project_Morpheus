# SCENES/README.md

> Scenes are executable probes that assert **behavioural shapes**.  
> They gate merges and document how the system should *feel* in operation.

## Principles

- **Shape over metric:** assert invariants and envelopes, not magic numbers.
- **Local artifacts:** each scene writes a JSON artifact with timings, counts, states.
- **Deterministic harness:** scenes are hermetic; they set up and tear down their own data.
- **Human-auditable:** artifacts are easy to read; failures tell a story.

## Common Scene Types (adapt to any stack)

- **Cold-Start:** new clone → install → run → succeeds without manual steps.
- **Long-Run:** sustained workload stabilizes; no unbounded growth in memory/handles.
- **Swap/Adapter:** two implementations of the same interface produce compatible results.
- **Failure Injection:** dependency latency/faults degrade gracefully and recover.
- **Concurrency:** parallel operations do not corrupt shared state.
- **Migration:** rolling upgrade with feature flags preserves old readers/writers.

## Scene Entry Template

### Scene: <name>
- **Intent:** <capability/goal it protects>
- **Shape:** <invariants asserted (e.g., “idempotent retry returns same result”)>
- **Setup:** <what it provisions>
- **Probe:** <what it does>
- **Artifacts:** `<path/to/json|log>` with keys: `{verdict, timings, notes}`
- **Gate:** required | optional

Place implementations under `SCENES/<scene_name>/` with a small runner.

