# ADAPTERS.md

> For any pluggable module (database driver, queue client, TTS engine, etc.), enforce a *capability descriptor* and a narrow interface.

## Rules

- **Single interface, many adapters:** no special-case branches in call sites.
- **Describe capabilities:** each adapter exposes a machine-readable descriptor.
- **Negotiate, don’t assume:** callers choose settings based on `describe()`, not hardcoded values.
- **Isolation:** heavy runtimes or native deps live behind process or thread boundaries.

## Descriptor (minimum)

```json
{
  "name": "<adapter>",
  "version": "x.y.z",
  "features": ["streaming","transactions","idempotency"],
  "limits": {"max_batch": 1000, "timeout_ms": 30000},
  "stateful_context": "rolling|minimal|none"
}

