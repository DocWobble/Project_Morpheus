import importlib.util
import sys
import types
from pathlib import Path


def _make_dummy_snac(called):
    class DummySNAC:
        @staticmethod
        def from_pretrained(name):
            called['name'] = name
            return DummySNAC()

        def eval(self):
            return self

        def to(self, device):
            return self

    dummy_module = types.ModuleType("snac")
    dummy_module.SNAC = DummySNAC
    return dummy_module


def _load_speechpipe():
    spec = importlib.util.spec_from_file_location(
        "Morpheus_Client.tts_engine.speechpipe",
        Path(__file__).resolve().parents[1] / "Morpheus_Client" / "tts_engine" / "speechpipe.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_snac_uses_env_path(monkeypatch, tmp_path):
    called = {}
    dummy_module = _make_dummy_snac(called)
    monkeypatch.setitem(sys.modules, "snac", dummy_module)
    dummy_path = tmp_path / "model"
    dummy_path.mkdir()
    monkeypatch.setenv("ORPHEUS_SNAC_PATH", str(dummy_path))

    sys.modules.pop("Morpheus_Client.tts_engine.speechpipe", None)
    _load_speechpipe()

    assert called["name"] == str(dummy_path)


def test_snac_uses_default_repo(monkeypatch):
    called = {}
    dummy_module = _make_dummy_snac(called)
    monkeypatch.setitem(sys.modules, "snac", dummy_module)
    monkeypatch.delenv("ORPHEUS_SNAC_PATH", raising=False)

    sys.modules.pop("Morpheus_Client.tts_engine.speechpipe", None)
    _load_speechpipe()

    assert called["name"] == "hubertsiuzdak/snac_24khz"
