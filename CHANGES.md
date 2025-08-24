# CHANGES

Capability-level changes between releases. Focus on user-facing deltas, not commit lists.

## [Unreleased]

- CLI now returns meaningful exit codes, enabling shell automation.
- Editing utilities avoid creating directories that already exist.
- Removed unused requirements and made `sounddevice` optional for server startup.
- Rewrote README with explicit virtual environment and one-click bootstrap instructions.
- One-click installer auto-detects CUDA/ROCm to install matching Torch, `llama-cpp-python`, and GPU extras.
