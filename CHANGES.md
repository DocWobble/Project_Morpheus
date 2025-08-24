# CHANGES

Capability-level changes between releases. Focus on user-facing deltas, not commit lists.

## [Unreleased]

- CLI now returns meaningful exit codes, enabling shell automation.
- Editing utilities avoid creating directories that already exist.
- Removed unused requirements and made `sounddevice` optional for server startup.
- Rewrote README with explicit virtual environment and one-click bootstrap instructions.
- `scripts/start.py` now injects the project root into `sys.path` so `Morpheus_Client` imports even when run from other directories.
