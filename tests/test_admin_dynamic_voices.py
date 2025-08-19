import os
import sys
import asyncio
from pathlib import Path
import httpx

# Ensure repo root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Morpheus_Client import app
from Morpheus_Client.tts_engine import AVAILABLE_VOICES
import re


def test_admin_voices_loaded_via_api():
    html_path = Path(__file__).resolve().parents[1] / "Morpheus_Client" / "admin" / "tts.html"
    html = html_path.read_text()

    # Voices are populated at runtime; representative names should not appear
    for voice in ("tara", "pierre"):
        assert re.search(rf"\b{re.escape(voice)}\b", html) is None

    # HTML should fetch voices dynamically
    assert "fetch('/v1/audio/voices')" in html

    async def fetch_voices():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/v1/audio/voices")

    resp = asyncio.run(fetch_voices())
    assert resp.status_code == 200
    data = resp.json()

    assert "voices" in data and isinstance(data["voices"], list)
    assert "languages" in data and isinstance(data["languages"], list)
    assert "voice_to_language" in data and isinstance(data["voice_to_language"], dict)

    first_voice = data["voices"][0]
    assert first_voice in AVAILABLE_VOICES
    assert data["voice_to_language"][first_voice] in data["languages"]
