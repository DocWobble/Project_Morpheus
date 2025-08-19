import builtins
import importlib
import pytest


def test_start_errors_when_orpheus_cpp_missing(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "orpheus_cpp":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    start = importlib.import_module("scripts.start")
    with pytest.raises(SystemExit) as exc:
        start.main()
    assert "orpheus_cpp is required" in str(exc.value)
