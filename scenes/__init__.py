"""Scenario harness for open-ended streaming tests.

This package exposes individual scene modules used by the test suite.  Each
scene is responsible for driving a mock :class:`~Morpheus_Client.orchestrator.adapter.TTSAdapter`
and writing a timeline JSON alongside a WAV artifact so the results can be
audited by humans and machines.

Only a tiny shim lives here – the heavy lifting is done in the sibling modules
(`barge_in`, `breathing_room`, `long_read` and `mid_stream_swap`).  Importing
them at package level keeps ``from scenes import …`` working while remaining a
light‑weight namespace.
"""

from . import barge_in, breathing_room, long_read, mid_stream_swap

__all__ = [
    "barge_in",
    "breathing_room",
    "long_read",
    "mid_stream_swap",
]

