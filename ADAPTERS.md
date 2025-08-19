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
```

## Text Source Adapters

Text sources implement the `TextSource` protocol and expose a descriptor for runtime negotiation.

### Protocol

```python
class TextSource(Protocol):
    async def stream(self) -> AsyncGenerator[str, None]:
        ...
```

### Descriptor

```json
{
  "name": "websocket|http_poll|cli_pipe",
  "streaming": true,
  "unit": "msgs",
  "granularity": ["line"],
  "stateful_context": "rolling|minimal|none"
}
```

Bundled adapters:

- `websocket` – reads messages from a WebSocket feed.
- `http_poll` – polls an HTTP endpoint for new text.
- `cli_pipe` – consumes lines from a CLI pipe via `asyncio`.
