import base64
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCENES = [
    "breathing_room",
    "long_read",
    "mid_stream_swap",
    "barge_in",
]

BUFFER_LIMIT_MS = 1000


def main(output_dir: str = "scenes_artifacts") -> int:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    ok = True
    for name in SCENES:
        mod = importlib.import_module(f"scenes.{name}")
        timeline_path, wav_path, _info = mod.run(out)
        with open(timeline_path, "r", encoding="utf-8") as fh:
            events = json.load(fh)
        for event in events:
            pcm = event.get("pcm")
            if not pcm:
                print(f"{name}: missing PCM data", file=sys.stderr)
                ok = False
            else:
                try:
                    base64.b64decode(pcm)
                except Exception:
                    print(f"{name}: non-base64 PCM detected", file=sys.stderr)
                    ok = False
            if any(key in event for key in ("path", "file")):
                print(f"{name}: found file path in event", file=sys.stderr)
                ok = False
            buf = event.get("buffer_ms")
            if buf is None or buf < 0 or buf > BUFFER_LIMIT_MS:
                print(f"{name}: buffer_ms {buf} out of range", file=sys.stderr)
                ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "scenes_artifacts"))
