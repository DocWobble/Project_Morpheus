"""Utilities for running Orpheus locally with a SNAC decoder.

This module lazily initialises an ``onnxruntime`` session for the
SNAC decoder model.  By default the model weights are downloaded from
Hugging Face using :func:`huggingface_hub.hf_hub_download`.  To make the
Hugging Face dependency optional, the download is only attempted when the
``ORPHEUS_SNAC_PATH`` environment variable is **not** set.  When the
variable is provided, it should point to either an ONNX file or a
directory containing one; that file will be used instead of contacting
Hugging Face.

The decoder session can also be injected (for example during testing)
via :func:`attach_decoder_session` rather than mutating the private
``_snac_session`` variable directly.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import onnxruntime as ort

# Repository and filename used when falling back to Hugging Face.  The
# actual contents are not exercised in the tests but are provided for
# completeness.
_SNAC_REPO = "hubertsiuzdak/snac_24khz"
_SNAC_FILENAME = "decoder.onnx"

# Internal global used to memoise the decoder session.
_snac_session: Optional[ort.InferenceSession] = None


def _resolve_snac_path() -> str:
    """Return the filesystem path to the SNAC ONNX model.

    If ``ORPHEUS_SNAC_PATH`` is set, that path is used directly.  If it
    points to a directory, the first ``*.onnx`` file inside is selected.
    Otherwise the file is downloaded from Hugging Face.  The
    ``huggingface_hub`` package is imported lazily so that the dependency
    is optional when a local path is provided.
    """

    env_path = os.environ.get("ORPHEUS_SNAC_PATH")
    if env_path:
        path = Path(env_path)
        if path.is_dir():
            candidates = list(path.glob("*.onnx"))
            if not candidates:
                raise FileNotFoundError(
                    f"No .onnx file found in directory: {path}")
            path = candidates[0]
        return str(path)

    # Only import huggingface_hub if we need to download the weights.
    from huggingface_hub import hf_hub_download  # type: ignore

    return hf_hub_download(repo_id=_SNAC_REPO, filename=_SNAC_FILENAME)


def get_decoder_session() -> ort.InferenceSession:
    """Return a cached ``onnxruntime.InferenceSession`` for the decoder."""
    global _snac_session
    if _snac_session is None:
        snac_path = _resolve_snac_path()
        _snac_session = ort.InferenceSession(snac_path)
    return _snac_session


def attach_decoder_session(session: Optional[ort.InferenceSession]) -> None:
    """Attach a pre-created decoder ``InferenceSession``.

    Passing ``None`` clears the cached session.  This provides a public
    hook for tests or advanced users to supply their own session without
    modifying the module's internal state directly.
    """
    global _snac_session
    _snac_session = session


__all__ = ["get_decoder_session", "attach_decoder_session"]
