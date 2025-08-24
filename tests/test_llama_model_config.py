import importlib
import os
import sys
import types


def make_dummy(record):
    class Dummy:
        def __init__(self, *, model_path, n_ctx, n_gpu_layers):
            record.update(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
            )

        def text_to_speech(self, *_args, **_kwargs):  # pragma: no cover - placeholder
            return iter([])

    return Dummy


def test_load_model_sync_uses_env(monkeypatch):
    record = {}
    dummy_module = types.SimpleNamespace(Llama=make_dummy(record))
    monkeypatch.setenv("LLAMA_MODEL_PATH", "foo.gguf")
    monkeypatch.setenv("LLAMA_N_CTX", "1234")
    monkeypatch.setenv("LLAMA_N_GPU_LAYERS", "5")
    monkeypatch.setitem(sys.modules, "llama_cpp", dummy_module)
    import Morpheus_Client.tts_engine.llama_local as llama_local
    importlib.reload(llama_local)
    llama_local._load_model_sync.cache_clear()
    llama_local._load_model_sync()
    assert record == {
        "model_path": "foo.gguf",
        "n_ctx": 1234,
        "n_gpu_layers": 5,
    }


def test_load_model_sync_defaults(monkeypatch):
    record = {}
    dummy_module = types.SimpleNamespace(Llama=make_dummy(record))
    monkeypatch.delenv("LLAMA_MODEL_PATH", raising=False)
    monkeypatch.delenv("LLAMA_N_CTX", raising=False)
    monkeypatch.delenv("LLAMA_N_GPU_LAYERS", raising=False)
    monkeypatch.setitem(sys.modules, "llama_cpp", dummy_module)
    import Morpheus_Client.tts_engine.llama_local as llama_local
    importlib.reload(llama_local)
    llama_local._load_model_sync.cache_clear()
    llama_local._load_model_sync()
    assert record == {
        "model_path": "model.gguf",
        "n_ctx": 8192,
        "n_gpu_layers": 0,
    }
