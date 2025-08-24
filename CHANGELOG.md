# Changelog

## Unreleased
- Refresh dependencies and relax version pins to minor ranges for patch updates
- Add lightweight orchestrator smoke tests and runner script
- Ignore Python bytecode caches and pytest cache

## Merge History
The Morpheus project merges functionality from the original **Orpheus-FastAPI** and **Orpheus-TTS** repositories. The list below captures each merged branch and how it advanced the combined codebase.

- **#1 – consolidate-token-to-audio-utilities**: Reused a shared speechpipe to remove duplicate token-to-audio logic across the separate repos.
- **#5 – refactor-create_speech_api-for-streaming-response**: Streamed audio responses directly instead of returning file paths from the FastAPI service.
- **#3 – fix-model-name-return-statement-and-add-unit-test**: Corrected model mapping and added tests so voice selection works uniformly.
- **#2 – modify-validate_voice-error-handling**: Validated requested voices against a local list, decoupling the API from remote voice sources.
- **#7 – resolve-pr-conflict-for-speech-generation**: Centralized the speechpipe decoder, avoiding diverging speech-generation flows between repos.
- **#8 – refactor-inference.py-to-use-async-httpx**: Replaced synchronous HTTP calls with async streaming, improving inference throughput.
- **#9 – refactor-handlers-to-stream-pcm/wav**: Emitted PCM/WAV streams with optional persistence, eliminating temporary audio files.
- **#10 – create-orchestrator-module-for-pcm-generation**: Introduced a PCM orchestrator with adaptive chunking to bridge request handling and TTS output.
- **#11 – review-agents.md-and-propose-optimal-approach**: Added orchestrator smoke tests and a runner script to vet the integrated stack.
- **#12 – review-agents.md-and-propose-optimal-approach (follow-up)**: Expanded smoke tests and documented the initial changelog.
- **#13 – implement-ttsadapter-and-update-app.py**: Implemented a generic TTSAdapter and barge-in control so multiple engines share a common interface.
- **#14 – add-ring-buffer-module-in-orchestrator**: Added a ring buffer with an adaptive chunk ladder to manage playback backpressure.
- **#15 – implement-adapter-registry-and-endpoints**: Introduced an adapter registry and config endpoints for hot-swapping TTS backends at runtime.
- **#16 – add-structured-logging-in-orchestrator**: Logged chunk metadata and enabled deterministic replay of generated audio.
- **#17 – emit-single-riff-header-for-streams**: Added an overlap-add stitcher and a single RIFF header for seamless WebSocket streaming.
- **#18 – add-scenes-package-with-tests-and-ci-integration**: Added scenario harness tests that produce timelines and audio artifacts to probe system behavior.
- **#19 – log-frame-data-and-create-replay-utility**: Logged per-frame metadata and provided a replay utility to audit audio generation.
- **#20 – add-scenes-package-with-tests**: Clarified scenes utility modules and tightened test coverage around the new scenario harness.

