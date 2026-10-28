
"""Command-line entry point for the lifecycle data pipeline."""

import argparse
import json
from pathlib import Path

from src.anomalies import inject_anomalies
from src.config import FULL_CONFIG, OUTPUT_DIR, STARTER_CONFIG, DatasetConfig
from src.exporter import export_dataset, export_labels, export_json
from src.generator import generate_master_data
from src.metrics import build_metrics, write_metrics
from src.validators import validate_data
from src.workflow import generate_dependent_records
from src.database import load_dataset


def build_dataset(config: DatasetConfig) -> dict[str, list[dict]]:
    """Generate master and dependent lifecycle records."""
    config.validate()
    master = generate_master_data(config)
    dependent = generate_dependent_records(master, config)
    return {**master, **dependent}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate and validate synthetic employee lifecycle data."
    )
    parser.add_argument(
        "--size",
        choices=("starter", "full"),
        default="starter",
        help="Dataset size to generate (default: starter).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed override.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory for generated outputs.",
    )
    args = parser.parse_args()

    base_config = STARTER_CONFIG if args.size == "starter" else FULL_CONFIG
    config = DatasetConfig(
        employees=base_config.employees,
        tasks=base_config.tasks,
        access_grants=base_config.access_grants,
        assets=base_config.assets,
        seed=base_config.seed if args.seed is None else args.seed,
    )

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating {args.size} dataset...")
    baseline = build_dataset(config)

    baseline_issues = validate_data(baseline)
    if baseline_issues:
        export_json(
            {"issues": baseline_issues},
            output_dir / "baseline_validation_issues.json",
        )
        raise SystemExit(
            f"Baseline validation failed with {len(baseline_issues)} issue(s)."
        )

    print("Baseline validation passed: zero issues.")
    baseline_db = output_dir / "baseline_lifecycle.db"
    load_dataset(baseline_db, baseline)
    print(f"Baseline SQLite database: {baseline_db}")

    print("Injecting labelled anomalies...")
    anomalous_data, labels = inject_anomalies(baseline)
    anomaly_issues = validate_data(anomalous_data)

    export_dataset(anomalous_data, output_dir, "anomalous")
    export_labels(labels, output_dir)

    export_json(
        {"issues": anomaly_issues},
        output_dir / "anomaly_validation_issues.json",
    )

    baseline_metrics = build_metrics(baseline, baseline_issues)
    anomaly_metrics = build_metrics(anomalous_data, anomaly_issues, labels)

    report = {
        "dataset_size": args.size,
        "seed": config.seed,
        "baseline": baseline_metrics,
        "anomalous": anomaly_metrics,
        "anomaly_types_injected": sorted({
            label.get("issue_type", "UNKNOWN") for label in labels
        }),
        "anomaly_types_detected": sorted({
            issue.get("issue_type", "UNKNOWN") for issue in anomaly_issues
        }),
    }

    write_metrics(report, output_dir / "metrics_report.json")

    print("\nPipeline completed successfully.")
    print(f"Output directory: {output_dir.resolve()}")
    print(f"Baseline records: {baseline_metrics['total_records']}")
    print(f"Anomaly ground-truth labels: {len(labels)}")
    print(f"Detected anomaly findings: {len(anomaly_issues)}")
    print(f"Metrics report: {output_dir / 'metrics_report.json'}")


if __name__ == "__main__":
    main()
