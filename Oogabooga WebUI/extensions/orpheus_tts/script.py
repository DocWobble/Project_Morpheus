import asyncio
import io
import logging
import wave

import gradio as gr
import numpy as np

logging.basicConfig(level=logging.INFO)

try:
    from Morpheus_Client.client import Client
    from Morpheus_Client.tts_engine import AVAILABLE_VOICES, DEFAULT_VOICE
    _client = Client()
    _import_error = None
except Exception as e:  # pragma: no cover - import failure is logged
    _client = None
    AVAILABLE_VOICES = []
    DEFAULT_VOICE = ""
    _import_error = str(e)
    logging.exception("Failed to import Morpheus_Client")

params = {
    "display_name": "Orpheus TTS",
    "is_tab": True,
}


def _speak(text: str, voice: str):
    if _client is None:
        msg = f"Morpheus_Client not available: {_import_error}"
        logging.error(msg)
        return (0, np.empty(0, dtype=np.int16)), msg

    async def _fetch():
        return b"".join(
            [chunk async for chunk in _client.stream_rest(text, voice=voice)]
        )

    try:
        wav_bytes = asyncio.run(_fetch())
        with wave.open(io.BytesIO(wav_bytes)) as wf:
            sr = wf.getframerate()
            audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        log_msg = "Generated audio successfully"
        return (sr, audio), log_msg
    except Exception as e:  # pragma: no cover - network failure
        logging.exception("TTS request failed")
        return (0, np.empty(0, dtype=np.int16)), str(e)


def ui() -> None:
    with gr.Column():
        log = gr.Textbox(label="Log", lines=4, value="", interactive=False)
        if _client is None:
            gr.Markdown(f"Failed to load Morpheus_Client: {_import_error}")
        else:
            api_url = _client.base_url.rstrip("/")
            gr.Markdown(
                f"Morpheus TTS running at `{api_url}`. [Docs]({api_url}/docs) · "
                f"[Admin]({api_url}/web/)"
            )
            text = gr.Textbox(label="Text", lines=2)
            voice = gr.Dropdown(
                list(AVAILABLE_VOICES), value=DEFAULT_VOICE, label="Voice"
            )
            speak = gr.Button("Speak")
            output = gr.Audio(label="Output", type="numpy")
            speak.click(_speak, inputs=[text, voice], outputs=[output, log])
