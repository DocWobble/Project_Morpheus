import builtins
import importlib
import pytest


def test_start_errors_when_llama_cpp_missing(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "llama_cpp":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    import sys
    sys.modules.pop("scripts.start", None)
    start = importlib.import_module("scripts.start")
    with pytest.raises(SystemExit) as exc:
        start.main()
    msg = str(exc.value)
    assert "pip install llama-cpp-python" in msg
    assert exc.value.__cause__ is None
