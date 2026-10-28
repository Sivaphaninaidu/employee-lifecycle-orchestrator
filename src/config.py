
"""Configuration for the employee lifecycle data generator."""

from dataclasses import dataclass
from pathlib import Path


# Project root: the directory containing src/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
DOCS_DIR = PROJECT_ROOT / "docs"

DEFAULT_SEED = 20261022


@dataclass(frozen=True)
class DatasetConfig:
    """Controls the size of a reproducible synthetic dataset."""

    employees: int = 1000
    tasks: int = 8000
    access_grants: int = 1500
    assets: int = 1200
    seed: int = DEFAULT_SEED

    def validate(self) -> None:
        """Reject invalid dataset sizes and seeds."""
        for name in ("employees", "tasks", "access_grants", "assets"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")

        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise ValueError("seed must be an integer")


STARTER_CONFIG = DatasetConfig(
    employees=25,
    tasks=200,
    access_grants=40,
    assets=30,
)

FULL_CONFIG = DatasetConfig()

# Create the output directory when the application starts.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
