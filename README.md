# Project Morpheus

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

### UI build
To build the optional web UI, install Node.js and npm then run within the UI directory (for example `Morpheus_Client/admin`):
```bash
npm install
npm run build
```
