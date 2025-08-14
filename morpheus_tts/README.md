# Morpheus TTS

`morpheus_tts` bundles the streaming orchestrator and TTS engine into a single
package with a tiny FastAPI server.  External scripts can either start the
server in-process or talk to a running instance using the bundled client.

## Starting the server

```python
import morpheus_tts

# Launches uvicorn and serves the API on 0.0.0.0:5005 by default
morpheus_tts.start_server()
```

## Using the client

The :class:`morpheus_tts.Client` provides helpers for both REST and WebSocket
streaming.

```python
import asyncio
from morpheus_tts import Client

async def main():
    client = Client("http://localhost:5005")

    # REST streaming
    async for chunk in client.stream_rest("Hello world"):
        ...  # handle WAV bytes

    # WebSocket streaming
    async for chunk in client.stream_ws("Hello again"):
        ...  # handle WAV bytes

asyncio.run(main())
```

The REST endpoint returns a streaming WAV response.  The WebSocket endpoint
first sends a WAV header followed by PCM frames.  Both methods yield raw bytes
that can be written to a file or played back incrementally.
