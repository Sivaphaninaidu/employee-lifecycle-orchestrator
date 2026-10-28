# Employee Lifecycle Orchestrator

A deterministic synthetic-data generator for modeling employee onboarding and offboarding workflows. The project generates related HR, task, access-control, and asset records; validates data integrity; injects labeled anomalies for testing; and exports datasets to JSON, CSV, and SQLite.

## Features

- Generates synthetic departments, roles, managers, employees, onboarding and offboarding cases, tasks, task dependencies, access roles, access grants, assets, and audit events.
- Supports starter and full dataset configurations.
- Uses configurable random seeds for reproducible generation.
- Validates primary-key uniqueness, foreign-key references, workflow dependencies, access grants, and asset assignments.
- Injects five categories of labeled anomalies without modifying the original baseline data.
- Exports baseline and anomalous datasets to JSON and CSV.
- Stores clean baseline records in SQLite.
- Produces validation findings and a JSON metrics report.

## Technology Stack

- Python
- SQLite
- CSV and JSON
- pytest

## Requirements

- Python 3.10 or newer
- pip

## Setup

Activate the virtual environment and install dependencies.

**Windows PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run the Project

Generate the starter dataset:

```powershell
python -m src.cli --size starter
```

Generate the full dataset in a separate output directory:

```powershell
python -m src.cli --size full --output-dir output/full_run
```

Specify a seed for reproducible generation:

```powershell
python -m src.cli --size starter --seed 12345
```

## Outputs

The selected output directory contains:

- `baseline/dataset.json` — clean records in JSON format.
- `baseline/csv/` — clean records as individual CSV files.
- `anomalous/dataset.json` — records with injected anomalies.
- `anomalous/csv/` — anomalous records as individual CSV files.
- `anomaly_labels.json` — ground-truth anomaly labels.
- `baseline_validation_issues.json` — baseline validation findings, if any.
- `anomaly_validation_issues.json` — findings detected in the anomalous dataset.
- `metrics_report.json` — record counts, issue counts, and anomaly metrics.
- `baseline_lifecycle.db` — SQLite database containing clean baseline records.

The anomalous dataset is exported for validation and testing. It is not loaded into the constrained SQLite schema because some injected anomalies intentionally violate database constraints.

## Dataset Configurations

- **Starter:** 25 employees, 200 tasks, 40 access grants, and 30 assets.
- **Full:** 1,000 employees, 8,000 tasks, 1,500 access grants, and 1,200 assets.

The total record count includes all generated entity collections, not only employees.

## Validation and Tests

Run the test suite:

```powershell
python -m pytest -v
```

The test suite contains 13 tests covering master-data generation, deterministic output, baseline validation, anomaly detection, input immutability, workflow record counts, and record references.

The full-size pipeline has been run successfully, with zero baseline validation issues, five injected anomaly labels, and eight findings reported by the validator.

## Design Decisions

- **Reproducibility:** deterministic seeds and fixed synthetic timestamps support repeatable results.
- **Separate ground truth:** anomaly labels are stored separately from the anomalous records.
- **Baseline versus anomalous data:** clean records and deliberately invalid records are exported separately.
- **Validation before anomaly injection:** the clean baseline is validated first.
- **SQLite constraints:** relational constraints protect stored baseline data, while intentionally invalid test data remains available in file exports.

## Limitations

- The records are synthetic and do not represent real employees.
- The workflows and anomaly patterns are illustrative rather than a complete enterprise HR platform.
- The test suite covers key functionality but is not exhaustive.
- A single injected anomaly can produce more than one validation finding.

## AI Assistance

AI tools were used to assist with implementation and development troubleshooting. The code was run and tested locally. See `PROMPT_HISTORY.md` for recorded prompts and development notes, if that file is included in the repository.

## License

No license has been selected yet. Add a license only after deciding how the repository may be used.
