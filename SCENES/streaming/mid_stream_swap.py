"""Runner for Mid-Stream Swap scene."""
from pathlib import Path

from scenes import mid_stream_swap


def main():  # pragma: no cover - manual runner
    artifact_dir = Path(__file__).parent / "_artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    mid_stream_swap.run(artifact_dir)


if __name__ == "__main__":  # pragma: no cover - script entry
    main()
