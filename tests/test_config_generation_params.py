import asyncio
import os

import httpx
import Morpheus_Client.server as server
from Morpheus_Client.tts_engine import inference
from Morpheus_Client.config import get_current_config


def test_generation_param_round_trip():
    orig_env = {k: os.environ.get(k) for k in ["ORPHEUS_TEMPERATURE", "ORPHEUS_TOP_P", "ORPHEUS_MAX_TOKENS"]}
    orig_vals = (inference.TEMPERATURE, inference.TOP_P, inference.MAX_TOKENS)

    async def run():
        transport = httpx.ASGITransport(app=server.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "ORPHEUS_TEMPERATURE": 0.7,
                "ORPHEUS_TOP_P": 0.8,
                "ORPHEUS_MAX_TOKENS": 1234,
            }
            resp = await client.post("/config", json=payload)
            assert resp.status_code == 200
            cfg_resp = await client.get("/config")
            return cfg_resp.json()

    try:
        config = asyncio.run(run())
        assert float(config["ORPHEUS_TEMPERATURE"]) == 0.7
        assert float(config["ORPHEUS_TOP_P"]) == 0.8
        assert int(config["ORPHEUS_MAX_TOKENS"]) == 1234
        assert inference.TEMPERATURE == 0.7
        assert inference.TOP_P == 0.8
        assert inference.MAX_TOKENS == 1234
        assert get_current_config()["ORPHEUS_TEMPERATURE"] == "0.7"
    finally:
        for key, val in orig_env.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val
        inference.update_generation_params(
            temperature=orig_vals[0], top_p=orig_vals[1], max_tokens=orig_vals[2]
        )
