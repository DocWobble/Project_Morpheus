import sys
from pathlib import Path

import pytest
import httpx
from unittest.mock import AsyncMock

# Ensure the package path is available
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Stub sounddevice to avoid PortAudio dependency during tests
import types
fake_sd = types.SimpleNamespace(play=lambda *a, **k: None, wait=lambda *a, **k: None)
sys.modules.setdefault("sounddevice", fake_sd)

from tts_engine import inference


@pytest.mark.asyncio
async def test_generate_tokens_from_api_retries_on_timeout(monkeypatch):
    """generate_tokens_from_api should retry on timeout and yield tokens."""
    lines = [
        'data: {"choices":[{"text":"hello"}]}',
        'data: [DONE]'
    ]

    class FakeTimeoutStream:
        async def __aenter__(self):
            raise httpx.TimeoutException("timeout")
        async def __aexit__(self, exc_type, exc, tb):
            pass

    class FakeStream:
        status_code = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def aiter_lines(self):
            for line in lines:
                yield line

        async def aread(self):
            return b""

    class FakeAsyncClient:
        calls = 0

        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def stream(self, *args, **kwargs):
            FakeAsyncClient.calls += 1
            if FakeAsyncClient.calls == 1:
                return FakeTimeoutStream()
            return FakeStream()

    async def fake_sleep(_):
        pass

    monkeypatch.setattr(inference.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(inference.asyncio, "sleep", fake_sleep)

    token_gen = inference.generate_tokens_from_api("hi")
    tokens = [token async for token in token_gen]

    assert tokens == ["hello>"]
    assert FakeAsyncClient.calls == 2


@pytest.mark.asyncio
async def test_generate_speech_from_api_produces_audio(monkeypatch):
    """generate_speech_from_api should return audio segments for short prompts."""

    async def fake_generate_tokens_from_api(*_, **__):
        for i in range(7):
            yield f"tok{i}>"

    def fake_turn_token_into_id(token, count):
        return count + 1

    def fake_convert_to_audio(multiframe, count):
        return b"audio" + bytes([len(multiframe)])

    monkeypatch.setattr(inference, "generate_tokens_from_api", fake_generate_tokens_from_api)
    monkeypatch.setattr(inference, "turn_token_into_id", fake_turn_token_into_id)
    monkeypatch.setattr(inference, "convert_to_audio", fake_convert_to_audio)

    segments = await inference.generate_speech_from_api("hello world", use_batching=False)

    assert len(segments) == 1
    assert segments[0].startswith(b"audio")


@pytest.mark.asyncio
async def test_generate_speech_from_api_batches_long_text(monkeypatch):
    """Long prompts should be split into batches and processed separately."""
    prompts = []

    def fake_generate_tokens_from_api(prompt, **kwargs):
        prompts.append(prompt)

        async def _gen():
            for i in range(7):
                yield f"{prompt}-{i}>"

        return _gen()

    mock_decoder = AsyncMock(return_value=[b"audio"])

    monkeypatch.setattr(inference, "generate_tokens_from_api", fake_generate_tokens_from_api)
    monkeypatch.setattr(inference, "tokens_decoder_sync", mock_decoder)

    long_prompt = "First sentence. Second sentence. Third sentence."
    await inference.generate_speech_from_api(long_prompt, use_batching=True, max_batch_chars=20)

    assert mock_decoder.await_count == 2
    assert prompts == ["First sentence. Second sentence.", "Third sentence."]
