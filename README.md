# Project Morpheus

## Overview

Single ASGI service exposing:

- `POST /v1/audio/speech` – streams WAV audio chunks
- `GET /v1/audio/voices` – lists available voices
- `GET /config` – returns current configuration
- `POST /config` – updates adapter, voice, text source or env vars and persists
- `GET /stats` – returns runtime telemetry and transcript history
- `GET /admin` – serves operator dashboard

The adapter registry defaults to a local speech synthesis adapter; remote backends are
optional and reside in a separate module. Responses are streamed as WAV audio
rather than text tokens.

## Installation

### Prerequisites
- Python 3.8–3.11
- Optional UI: Node.js ≥18 and npm

### Base setup
```bash
pip install -r requirements.txt
```

### Hardware-specific notes
- **NVIDIA CUDA**
  ```bash
  pip install torch==2.2.0 --extra-index-url https://download.pytorch.org/whl/cu124
  pip install bitsandbytes==0.46.1 flash-attn==2.7.4.post1
  ```
- **AMD ROCm**
  ```bash
  pip install torch==2.2.0 --extra-index-url https://download.pytorch.org/whl/rocm6.2
  ```
- **CPU only**
  ```bash
  pip install torch==2.2.0
  ```

### C++ bindings
The local streaming adapter uses `orpheus_cpp`, which builds a native extension. Ensure a C++17 toolchain and CMake are available (e.g. `sudo apt install build-essential cmake` on Linux or [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) on Windows) before installing:

```bash
pip install orpheus-cpp
```

This dependency is pinned in `requirements.txt`; the build step may take several minutes.

### UI build
To build the optional web UI, install Node.js and npm then run within the UI directory (for example `Morpheus_Client/admin`):
```bash
npm install
npm run build
```

### Run
Start the server and open the admin UI:
```bash
python scripts/start.py
```
The service listens on `http://localhost:5005` and hosts the dashboard at
`http://localhost:5005/admin`.

### Client
Use the bundled client to consume streamed audio:
```python
import asyncio
from Morpheus_Client import Client

async def main():
    client = Client("http://localhost:5005")
    with open("output.wav", "wb") as f:
        async for chunk in client.stream_rest("Hello world"):
            f.write(chunk)

asyncio.run(main())
```
