"""Streaming scene tests verifying buffer and latency shapes."""
import os
from pathlib import Path

import pytest

from scenes import barge_in, cold_start, long_read, mid_stream_swap


@pytest.fixture
def artifact_dir(tmp_path):
    base = os.environ.get("SCENES_ARTIFACT_DIR")
    if base:
        path = Path(base)
    else:
        path = Path("SCENES/_artifacts/streaming")
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_cold_start(artifact_dir):
    timeline_path, wav_path, info = cold_start.run(artifact_dir)
    assert timeline_path.exists()
    assert wav_path.exists()
    timeline = info["timeline"]
    assert len(timeline) >= 2
    first, second = timeline[0], timeline[1]
    assert first["render_ms"] > second["render_ms"]
    assert all(t["buffer_ms"] >= 0 for t in timeline)


def test_long_read(artifact_dir):
    timeline_path, wav_path, info = long_read.run(artifact_dir)
    assert timeline_path.exists()
    assert wav_path.exists()
    timeline = info["timeline"]
    assert len(timeline) >= 50
    durations = {t["duration_ms"] for t in timeline}
    assert len(durations) == 1
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
    assert all(t["buffer_ms"] >= 0 for t in info["timeline"])


def test_barge_in(artifact_dir):
    timeline_path, wav_path, info = barge_in.run(artifact_dir)
    assert timeline_path.exists()
    assert wav_path.exists()
    assert info["reset_called"]
    assert len(info["timeline"]) < info["planned_chunks"]
    assert all(t["buffer_ms"] >= 0 for t in info["timeline"])
