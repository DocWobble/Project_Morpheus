from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from Morpheus_Client.config import router as config_router, ensure_env_file_exists
from morpheus_tts.tts_engine import AVAILABLE_VOICES
from morpheus_tts.tts_engine.adapter_registry import registry as adapter_registry

# Ensure environment variables are loaded from .env
ensure_env_file_exists()
load_dotenv(override=True)

app = FastAPI()
app.include_router(config_router)


@app.get("/v1/audio/voices")
async def list_voices():
    """Return list of available voices."""
    if not AVAILABLE_VOICES:
        raise HTTPException(status_code=404, detail="No voices available")
    return JSONResponse(content={"status": "ok", "voices": AVAILABLE_VOICES})


@app.get("/adapters")
async def get_adapters():
    """Expose capability descriptors for all available adapters."""
    return adapter_registry.available()
