import builtins
import importlib
import types
import sys
import pytest


def test_start_errors_when_dotenv_missing(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "dotenv":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setitem(sys.modules, "llama_cpp", types.SimpleNamespace())
    # Ensure module is reloaded even if previously imported
    sys.modules.pop("scripts.start", None)
    with pytest.raises(SystemExit) as exc:
        importlib.import_module("scripts.start")
    msg = str(exc.value)
    assert "pip install python-dotenv" in msg
    assert exc.value.__cause__ is None
