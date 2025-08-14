"""Open-ended scenario tests producing audit artefacts.

If the environment variable ``SCENES_ARTIFACT_DIR`` is set, the generated
timeline JSON and WAV files are written there so they can be collected by CI
or inspected manually.  Otherwise they are created inside pytest's temporary
directory like a normal unit test.
"""

import os
from pathlib import Path

import pytest

from scenes import barge_in, breathing_room, long_read, mid_stream_swap


@pytest.fixture
def artifact_dir(tmp_path):
    """Return output directory for scene artefacts.

    The default is pytest's ``tmp_path`` but callers may override this by
    setting ``SCENES_ARTIFACT_DIR`` in the environment.
    """

    base = os.environ.get("SCENES_ARTIFACT_DIR")
    if base:
        path = Path(base)
        path.mkdir(parents=True, exist_ok=True)
        return path
    return tmp_path


def test_breathing_room(artifact_dir):
    timeline_path, wav_path, info = breathing_room.run(artifact_dir)
    assert timeline_path.exists()
    assert wav_path.exists()
    timeline = info["timeline"]
    assert len(timeline) >= 2
    assert timeline[0]["chunk_id"] == 0


def test_long_read(artifact_dir):
    timeline_path, wav_path, info = long_read.run(artifact_dir)
    assert timeline_path.exists()
    assert wav_path.exists()
    timeline = info["timeline"]
    assert len(timeline) >= 50
    durations = {t["duration_ms"] for t in timeline}
    assert len(durations) == 1  # converged chunk size
    assert all(t["buffer_ms"] >= 0 for t in timeline)


def test_mid_stream_swap(artifact_dir):
    timeline_path, wav_path, info = mid_stream_swap.run(artifact_dir)
    assert timeline_path.exists()
    assert wav_path.exists()
    adapters = [t["adapter"] for t in info["timeline"]]
    assert "adapter_a" in adapters and "adapter_b" in adapters
    idx = adapters.index("adapter_b")
    assert all(a == "adapter_a" for a in adapters[:idx])
    assert all(a == "adapter_b" for a in adapters[idx:])


def test_barge_in(artifact_dir):
    timeline_path, wav_path, info = barge_in.run(artifact_dir)
    assert timeline_path.exists()
    assert wav_path.exists()
    assert info["reset_called"]
    assert len(info["timeline"]) < info["planned_chunks"]
