
"""Export generated lifecycle datasets to JSON and CSV files."""

import csv
import json
from pathlib import Path
from typing import Any


def _json_default(value: Any) -> str:
    """Convert values not directly supported by JSON."""
    return str(value)


def export_json(data: dict[str, list[dict]], path: Path) -> None:
    """Write a dataset dictionary to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, default=_json_default)
        file.write("\n")


def export_csv(data: dict[str, list[dict]], output_dir: Path) -> None:
    """Write one CSV file per entity."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for entity_name, records in data.items():
        if not records:
            continue

        # Keep a consistent column order based on the first occurrence.
        columns = list(dict.fromkeys(
            key for record in records for key in record.keys()
        ))
        file_path = output_dir / f"{entity_name}.csv"

        with file_path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=columns,
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(records)


def export_dataset(
    data: dict[str, list[dict]],
    output_dir: Path,
    dataset_name: str,
) -> None:
    """Export a named dataset in JSON and CSV formats."""
    dataset_dir = output_dir / dataset_name
    dataset_dir.mkdir(parents=True, exist_ok=True)

    export_json(data, dataset_dir / "dataset.json")
    export_csv(data, dataset_dir / "csv")


def export_labels(labels: list[dict], output_dir: Path) -> None:
    """Store anomaly ground-truth labels separately from dataset records."""
    output_dir.mkdir(parents=True, exist_ok=True)
    export_json({"labels": labels}, output_dir / "anomaly_labels.json")
