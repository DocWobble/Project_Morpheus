# Requirements Installation

The repository provides environment-specific requirement files in `requirements/full`.

Use the appropriate file for your hardware:

- **NVIDIA CUDA:** `pip install -r requirements/full/requirements_cuda.txt`
- **AMD ROCm:** `pip install -r requirements/full/requirements_rocm.txt`
- **CPU only:** `pip install -r requirements/full/requirements_cpu.txt`
- **Apple Silicon:** `pip install -r requirements/full/requirements_apple_silicon.txt`
- **Apple Intel:** `pip install -r requirements/full/requirements_apple_intel.txt`

Alternatively, run the installer script to auto-detect and install:

```bash
python scripts/install.py
```
