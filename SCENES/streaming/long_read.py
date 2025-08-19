"""Runner for Long Read scene."""
from pathlib import Path

from scenes import long_read


def main():  # pragma: no cover - manual runner
    artifact_dir = Path(__file__).parent / "_artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    long_read.run(artifact_dir)


if __name__ == "__main__":  # pragma: no cover - script entry
    main()
