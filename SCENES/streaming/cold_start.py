"""Runner for Cold Start scene."""
from pathlib import Path

from scenes import cold_start


def main():  # pragma: no cover - manual runner
    artifact_dir = Path(__file__).parent / "_artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    cold_start.run(artifact_dir)


if __name__ == "__main__":  # pragma: no cover - script entry
    main()
