"""Orpheus Text-to-Speech System."""

__version__ = "0.1.0"

from morpheus_tts.tts_engine.speechpipe import tokens_decoder_sync
from .engine_class import OrpheusModel

__all__ = ["tokens_decoder_sync", "OrpheusModel"]
