#!/usr/bin/env python3
"""Rebuild audio from orchestrator timeline logs."""

import argparse
import base64
import json
import wave


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild audio from timeline JSON logs")
    parser.add_argument(
        "log", help="Path to timeline log (JSON lines or array)"
    )
    parser.add_argument(
        "-o", "--out", default="replay.wav", help="Destination WAV file"
    )
    parser.add_argument(
        "--sample-rate", type=int, default=16000, help="PCM sample rate in Hz"
    )
    args = parser.parse_args()

    pcm = bytearray()
    with open(args.log, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if content.startswith("["):
        events = json.loads(content)
    else:
        events = [json.loads(line) for line in content.splitlines() if line]
    for event in events:
        data = event.get("pcm")
        if data:
            pcm.extend(base64.b64decode(data))

    with wave.open(args.out, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(args.sample_rate)
        wf.writeframes(pcm)


if __name__ == "__main__":
    main()
