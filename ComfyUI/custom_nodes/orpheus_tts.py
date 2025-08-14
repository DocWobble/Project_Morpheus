import asyncio
import logging

logging.basicConfig(level=logging.INFO)

try:
    from morpheus_tts.client import Client
    from morpheus_tts.tts_engine import DEFAULT_VOICE
    _import_error = None
except Exception as e:  # pragma: no cover - import failure is logged
    Client = None
    DEFAULT_VOICE = ""
    _import_error = e
    logging.exception("Failed to import morpheus_tts")


class OrpheusTTSNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
                "voice": ("STRING", {"default": DEFAULT_VOICE}),
                "base_url": ("STRING", {"default": "http://localhost:5005"}),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "generate"
    CATEGORY = "morpheus"

    def __init__(self):
        self._client = None
        self._base_url = None

    def generate(self, text: str, voice: str, base_url: str):
        if Client is None:
            msg = f"morpheus_tts not available: {_import_error}"
            logging.error(msg)
            raise RuntimeError(msg)

        base = base_url.rstrip("/")
        if self._client is None or self._base_url != base:
            self._client = Client(base)
            self._base_url = base

        async def _fetch():
            return b"".join(
                [chunk async for chunk in self._client.stream_rest(text, voice=voice)]
            )

        try:
            audio_bytes = asyncio.run(_fetch())
        except Exception as e:  # pragma: no cover - network failure
            logging.exception("TTS request failed")
            raise RuntimeError(str(e))
        return ({"audio": audio_bytes, "mime": "audio/wav"},)


NODE_CLASS_MAPPINGS = {"OrpheusTTS": OrpheusTTSNode}
NODE_DISPLAY_NAME_MAPPINGS = {"OrpheusTTS": "Orpheus TTS"}
