import importlib
import sys
import types

import pytest


def test_env_local_path(monkeypatch, tmp_path):
    # Stub dependencies that have heavy import-time requirements
    dummy_sd = types.SimpleNamespace(play=lambda *a, **k: None, wait=lambda: None)
    monkeypatch.setitem(sys.modules, "sounddevice", dummy_sd)

    dummy_ort = types.SimpleNamespace(InferenceSession=None)
    monkeypatch.setitem(sys.modules, "onnxruntime", dummy_ort)

    import morpheus_tts.tts_engine.orpheus_local as ol
    importlib.reload(ol)

    # Create fake ONNX file and point env var to it
    onnx_file = tmp_path / "decoder.onnx"
    onnx_file.write_text("fake")
    monkeypatch.setenv("ORPHEUS_SNAC_PATH", str(onnx_file))

    seen = {}

    class DummySession:
        def __init__(self, path):
            seen["path"] = path

    monkeypatch.setattr(ol.ort, "InferenceSession", DummySession)

    # Ensure huggingface_hub would fail if imported
    monkeypatch.setitem(sys.modules, "huggingface_hub", None)

    ol.attach_decoder_session(None)
    session = ol.get_decoder_session()
    assert isinstance(session, DummySession)
    assert seen["path"] == str(onnx_file)
    assert "huggingface_hub" not in sys.modules or sys.modules["huggingface_hub"] is None
