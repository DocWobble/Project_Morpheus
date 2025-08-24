import importlib
import os
import sys
import types


def make_dummy(record):
    class Dummy:
        def __init__(self, *, verbose, lang, n_ctx, n_gpu_layers):
            record.update(
                verbose=verbose,
                lang=lang,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
            )
    return Dummy


def test_load_model_sync_uses_env(monkeypatch):
    record = {}
    dummy_module = types.SimpleNamespace(OrpheusCpp=make_dummy(record))
    monkeypatch.setenv("ORPHEUS_N_CTX", "1234")
    monkeypatch.setenv("ORPHEUS_N_GPU_LAYERS", "5")
    monkeypatch.setitem(sys.modules, "orpheus_cpp", dummy_module)
    import Morpheus_Client.tts_engine.orpheus_local as orpheus_local
    importlib.reload(orpheus_local)
    orpheus_local._load_model_sync.cache_clear()
    orpheus_local._load_model_sync()
    assert record == {
        "verbose": False,
        "lang": "en",
        "n_ctx": 1234,
        "n_gpu_layers": 5,
    }


def test_load_model_sync_defaults(monkeypatch):
    record = {}
    dummy_module = types.SimpleNamespace(OrpheusCpp=make_dummy(record))
    monkeypatch.delenv("ORPHEUS_N_CTX", raising=False)
    monkeypatch.delenv("ORPHEUS_N_GPU_LAYERS", raising=False)
    monkeypatch.setitem(sys.modules, "orpheus_cpp", dummy_module)
    import Morpheus_Client.tts_engine.orpheus_local as orpheus_local
    importlib.reload(orpheus_local)
    orpheus_local._load_model_sync.cache_clear()
    orpheus_local._load_model_sync()
    assert record == {
        "verbose": False,
        "lang": "en",
        "n_ctx": 8192,
        "n_gpu_layers": 0,
    }
