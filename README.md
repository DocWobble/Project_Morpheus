# Project Morpheus

ASGI service that converts text input into streamed WAV audio using the Orpheus TTS engine.

## Quick Start

### Manual setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# install the Torch build for your hardware BEFORE other requirements
# NVIDIA CUDA
pip install torch==2.2.0 --extra-index-url https://download.pytorch.org/whl/cu124
pip install bitsandbytes==0.46.1 flash-attn==2.7.4.post1
# AMD ROCm
# pip install torch==2.2.0 --extra-index-url https://download.pytorch.org/whl/rocm6.2
# CPU only
# pip install torch==2.2.0

pip install -r requirements.txt
python scripts/start.py
```

After the server prints that it is running, verify audio streaming:

```bash
curl -L -X POST http://localhost:5005/v1/audio/speech \
     -H "Content-Type: text/plain" \
     --data 'Hello world' -o output.wav
```

Play `output.wav` with any media player.

### One-click setup

```bash
python scripts/one_click.py
python scripts/start.py
```

`one_click.py` downloads Miniforge if needed, creates a virtual environment and installs all requirements.

The admin dashboard is served at http://localhost:5005/admin.

## Prerequisites

- Python 3.8–3.11
- C++17 toolchain and CMake for building `orpheus-cpp` (e.g. `sudo apt install build-essential cmake`)
- The `orpheus-cpp` build step during installation may take several minutes.

## Client example

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
