
"""Metrics and summary reports for lifecycle datasets."""

from collections import Counter
from pathlib import Path
import json


def build_metrics(
    data: dict[str, list[dict]],
    validation_issues: list[dict],
    anomaly_labels: list[dict] | None = None,
) -> dict:
    """Build a compact summary of dataset size and validation results."""
    anomaly_labels = anomaly_labels or []

    record_counts = {
        entity_name: len(records)
        for entity_name, records in sorted(data.items())
    }

    issue_counts = dict(sorted(Counter(
        issue.get("issue_type", "UNKNOWN")
        for issue in validation_issues
    ).items()))

    label_counts = dict(sorted(Counter(
        label.get("issue_type", "UNKNOWN")
        for label in anomaly_labels
    ).items()))

    return {
        "record_counts": record_counts,
        "total_records": sum(record_counts.values()),
        "validation_issue_count": len(validation_issues),
        "validation_issue_counts_by_type": issue_counts,
        "ground_truth_label_count": len(anomaly_labels),
        "ground_truth_labels_by_type": label_counts,
    }


def write_metrics(metrics: dict, path: Path) -> None:
    """Write metrics to a readable JSON report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)
        file.write("\n")
