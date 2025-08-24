import platform
import shutil
import sys
from pathlib import Path

from scripts import one_click


def test_miniforge_detection_and_skip(tmp_path, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: None)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    (tmp_path / "miniforge3").mkdir()
    assert one_click.miniforge_installed() is True
    # Should exit early without attempting download
    one_click.install_miniforge("Linux", "x86_64")


def test_ensure_venv_creates_and_returns_python(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls = []

    def fake_call(cmd):
        calls.append(cmd)
        (tmp_path / ".venv").mkdir()

    monkeypatch.setattr(one_click.subprocess, "check_call", fake_call)
    python = one_click.ensure_venv()
    assert calls[0][:3] == [sys.executable, "-m", "venv"]
    expected = Path(".venv") / ("Scripts" if platform.system().lower() == "windows" else "bin") / ("python.exe" if platform.system().lower() == "windows" else "python")
    assert python == expected


def test_install_requirements_uses_given_python(tmp_path, monkeypatch):
    req = tmp_path / "requirements.txt"
    req.write_text("")
    calls = []

    def fake_call(cmd):
        calls.append(cmd)

    monkeypatch.setattr(one_click.subprocess, "check_call", fake_call)
    python = tmp_path / "custom" / "python"
    one_click.install_requirements(python, req)
    assert calls[0][0] == str(python)
