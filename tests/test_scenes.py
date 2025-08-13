from scenes import barge_in, breathing_room, long_read, mid_stream_swap


def test_breathing_room(tmp_path):
    timeline_path, wav_path, info = breathing_room.run(tmp_path)
    assert timeline_path.exists()
    assert wav_path.exists()
    timeline = info["timeline"]
    assert len(timeline) >= 2
    assert timeline[0]["chunk_id"] == 0


def test_long_read(tmp_path):
    timeline_path, wav_path, info = long_read.run(tmp_path)
    assert timeline_path.exists()
    assert wav_path.exists()
    timeline = info["timeline"]
    assert len(timeline) >= 50
    durations = {t["duration_ms"] for t in timeline}
    assert len(durations) == 1  # converged chunk size
    assert all(t["buffer_ms"] >= 0 for t in timeline)


def test_mid_stream_swap(tmp_path):
    timeline_path, wav_path, info = mid_stream_swap.run(tmp_path)
    assert timeline_path.exists()
    assert wav_path.exists()
    adapters = [t["adapter"] for t in info["timeline"]]
    assert "adapter_a" in adapters and "adapter_b" in adapters
    idx = adapters.index("adapter_b")
    assert all(a == "adapter_a" for a in adapters[:idx])
    assert all(a == "adapter_b" for a in adapters[idx:])


def test_barge_in(tmp_path):
    timeline_path, wav_path, info = barge_in.run(tmp_path)
    assert timeline_path.exists()
    assert wav_path.exists()
    assert info["reset_called"]
    assert len(info["timeline"]) < info["planned_chunks"]
