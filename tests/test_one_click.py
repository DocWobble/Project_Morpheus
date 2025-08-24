import shutil
from pathlib import Path

from scripts import one_click


def test_detect_gpu_cuda(monkeypatch):
    monkeypatch.setattr(
        shutil, "which", lambda name: "/usr/bin/nvidia-smi" if name == "nvidia-smi" else None
    )
    assert one_click.detect_gpu() == "cuda"


def test_detect_gpu_rocm(monkeypatch):
    monkeypatch.setattr(
        shutil, "which", lambda name: "/opt/rocm/bin/rocm-smi" if name == "rocm-smi" else None
    )
    assert one_click.detect_gpu() == "rocm"


def test_install_torch_cuda(monkeypatch):
    calls = []
    monkeypatch.setattr(one_click.subprocess, "check_call", lambda cmd: calls.append(cmd))
    one_click.install_torch("cuda")
    assert calls[0][-2:] == ["--extra-index-url", "https://download.pytorch.org/whl/cu124"]
    assert calls[1][4:] == ["bitsandbytes", "flash-attn"]


def test_install_llama_cpp_cpu(monkeypatch):
    calls = []
    monkeypatch.setattr(one_click.subprocess, "check_call", lambda cmd: calls.append(cmd))
    one_click.install_llama_cpp(None)
    assert calls[0] == [
        one_click.sys.executable,
        "-m",
        "pip",
        "install",
        "llama-cpp-python",
    ]


def test_miniforge_detection_and_skip(tmp_path, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: None)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    (tmp_path / "miniforge3").mkdir()
    assert one_click.miniforge_installed() is True
    # Should exit early without attempting download
    one_click.install_miniforge("Linux", "x86_64")
