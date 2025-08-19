"""Utilities for talking to a remote Orpheus backend."""

from __future__ import annotations

import argparse
import asyncio
import os
import json
import sys
import time
import wave
from typing import AsyncGenerator

import httpx
import torch
from dotenv import load_dotenv

from .inference import (
    PerformanceMonitor,
    format_prompt,
    split_text_into_sentences,
    DEFAULT_VOICE,
    HIGH_END_GPU,
    TEMPERATURE,
    TOP_P,
    MAX_TOKENS,
    REPETITION_PENALTY,
    SAMPLE_RATE,
)
from .speechpipe import tokens_decoder, tokens_decoder_sync

load_dotenv()

API_URL = os.environ.get("ORPHEUS_API_URL")
HEADERS = {"Content-Type": "application/json"}

try:
    REQUEST_TIMEOUT = int(os.environ.get("ORPHEUS_API_TIMEOUT", "120"))
except (ValueError, TypeError):
    REQUEST_TIMEOUT = 120

perf_monitor = PerformanceMonitor()


async def generate_tokens_from_api(
    prompt: str,
    voice: str = DEFAULT_VOICE,
    temperature: float = TEMPERATURE,
    top_p: float = TOP_P,
    max_tokens: int = MAX_TOKENS,
    repetition_penalty: float = REPETITION_PENALTY,
) -> AsyncGenerator[str, None]:
    """Stream tokens from a remote API compatible with the OpenAI spec."""

    start_time = time.time()
    formatted_prompt = format_prompt(prompt, voice)
    print(f"Generating speech for: {formatted_prompt}")

    if HIGH_END_GPU:
        print("Using optimized parameters for high-end GPU")
    elif torch.cuda.is_available():
        print("Using optimized parameters for GPU acceleration")

    payload = {
        "prompt": formatted_prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "repeat_penalty": repetition_penalty,
        "stream": True,
    }

    model_name = os.environ.get("ORPHEUS_MODEL_NAME", "Orpheus-3b-FT-Q8_0.gguf")
    payload["model"] = model_name

    retry_count = 0
    max_retries = 3

    async with httpx.AsyncClient() as client:
        while retry_count < max_retries:
            try:
                async with client.stream(
                    "POST",
                    API_URL,
                    headers=HEADERS,
                    json=payload,
                    timeout=REQUEST_TIMEOUT,
                ) as response:
                    if response.status_code != 200:
                        print(
                            f"Error: API request failed with status code {response.status_code}"
                        )
                        print(f"Error details: {await response.aread()}")
                        if response.status_code >= 500:
                            retry_count += 1
                            wait_time = 2 ** retry_count
                            print(f"Retrying in {wait_time} seconds...")
                            await asyncio.sleep(wait_time)
                            continue
                        return

                    token_counter = 0
                    async for line in response.aiter_lines():
                        if line and line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                if "choices" in data and data["choices"]:
                                    token_chunk = data["choices"][0].get("text", "")
                                    for token_text in token_chunk.split(">"):
                                        token_text = f"{token_text}>"
                                        token_counter += 1
                                        perf_monitor.add_tokens()
                                        if token_text:
                                            yield token_text
                            except json.JSONDecodeError as e:
                                print(f"Error decoding JSON: {e}")
                                continue

                    generation_time = time.time() - start_time
                    tokens_per_second = (
                        token_counter / generation_time if generation_time > 0 else 0
                    )
                    print(
                        f"Token generation complete: {token_counter} tokens in {generation_time:.2f}s ({tokens_per_second:.1f} tokens/sec)"
                    )
                    return

            except httpx.TimeoutException:
                print(f"Request timed out after {REQUEST_TIMEOUT} seconds")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count
                    print(
                        f"Retrying in {wait_time} seconds... (attempt {retry_count+1}/{max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    print("Max retries reached. Token generation failed.")
                    return
            except httpx.RequestError:
                print(f"Connection error to API at {API_URL}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count
                    print(
                        f"Retrying in {wait_time} seconds... (attempt {retry_count+1}/{max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    print("Max retries reached. Token generation failed.")
                    return


async def generate_speech_from_api(
    prompt,
    voice=DEFAULT_VOICE,
    output_file=None,
    temperature=TEMPERATURE,
    top_p=TOP_P,
    max_tokens=MAX_TOKENS,
    repetition_penalty=None,
    use_batching=True,
    max_batch_chars=1000,
):
    """Generate speech from text via the remote API."""

    print(
        f"Starting speech generation for '{prompt[:50]}{'...' if len(prompt) > 50 else ''}'"
    )
    print(
        f"Using voice: {voice}, GPU acceleration: {'Yes (High-end)' if HIGH_END_GPU else 'Yes' if torch.cuda.is_available() else 'No'}"
    )

    global perf_monitor
    perf_monitor = PerformanceMonitor()

    start_time = time.time()

    async def _stream_batches(batches):
        for batch in batches:
            token_gen = generate_tokens_from_api(
                prompt=batch,
                voice=voice,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                repetition_penalty=REPETITION_PENALTY,
            )
            async for chunk in tokens_decoder(token_gen):
                yield chunk

    if output_file:
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        audio_segments = []
        with wave.open(output_file, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(SAMPLE_RATE)
            async for chunk in tokens_decoder_sync(
                generate_tokens_from_api(
                    prompt=prompt,
                    voice=voice,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    repetition_penalty=REPETITION_PENALTY,
                )
            ):
                if chunk:
                    wav_file.writeframes(chunk)
                    audio_segments.append(chunk)

        end_time = time.time()
        total_time = end_time - start_time
        print(f"Total speech generation completed in {total_time:.2f} seconds")
        return audio_segments

    batches = [prompt]
    if use_batching and len(prompt) >= max_batch_chars:
        print(
            f"Using sentence-based batching for text with {len(prompt)} characters"
        )
        sentences = split_text_into_sentences(prompt)
        current_batch = ""
        batches = []
        for sentence in sentences:
            if len(current_batch) + len(sentence) > max_batch_chars and current_batch:
                batches.append(current_batch)
                current_batch = sentence
            else:
                if current_batch:
                    current_batch += " "
                current_batch += sentence
        if current_batch:
            batches.append(current_batch)
        print(f"Created {len(batches)} batches for processing")

    return _stream_batches(batches)


def main() -> None:  # pragma: no cover - CLI utility
    parser = argparse.ArgumentParser(
        description="Orpheus Text-to-Speech using Orpheus-FASTAPI"
    )
    parser.add_argument("--text", type=str, help="Text to convert to speech")
    parser.add_argument(
        "--voice",
        type=str,
        default=DEFAULT_VOICE,
        help=f"Voice to use (default: {DEFAULT_VOICE})",
    )
    parser.add_argument("--output", type=str, help="Output WAV file path")
    parser.add_argument("--list-voices", action="store_true", help="List available voices")
    parser.add_argument(
        "--temperature",
        type=float,
        default=TEMPERATURE,
        help="Temperature for generation",
    )
    parser.add_argument(
        "--top_p", type=float, default=TOP_P, help="Top-p sampling parameter"
    )
    parser.add_argument(
        "--repetition_penalty",
        type=float,
        default=REPETITION_PENALTY,
        help="Repetition penalty (fixed at 1.1 for stable generation)",
    )

    args = parser.parse_args()

    if args.list_voices:
        from .inference import list_available_voices

        list_available_voices()
        return

    prompt = args.text
    if not prompt:
        if len(sys.argv) > 1 and sys.argv[1] not in (
            "--voice",
            "--output",
            "--temperature",
            "--top_p",
            "--repetition_penalty",
        ):
            prompt = " ".join([arg for arg in sys.argv[1:] if not arg.startswith("--")])
        else:
            prompt = input("Enter text to synthesize: ")
            if not prompt:
                prompt = (
                    "Hello, I am Orpheus, an AI assistant with emotional speech capabilities."
                )

    output_file = args.output
    if not output_file:
        os.makedirs("outputs", exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f"outputs/{args.voice}_{timestamp}.wav"
        print(f"No output file specified. Saving to {output_file}")

    start_time = time.time()
    audio_segments = asyncio.run(
        generate_speech_from_api(
            prompt=prompt,
            voice=args.voice,
            temperature=args.temperature,
            top_p=args.top_p,
            repetition_penalty=args.repetition_penalty,
            output_file=output_file,
        )
    )
    end_time = time.time()

    print(f"Speech generation completed in {end_time - start_time:.2f} seconds")
    print(f"Audio saved to {output_file}")


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()

