import shutil
from pathlib import Path

from scripts import one_click


def test_miniforge_detection_and_skip(tmp_path, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: None)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    (tmp_path / "miniforge3").mkdir()
    assert one_click.miniforge_installed() is True
    # Should exit early without attempting download
    one_click.install_miniforge("Linux", "x86_64")
