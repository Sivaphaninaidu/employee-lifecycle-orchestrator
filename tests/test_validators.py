from copy import deepcopy

from src.config import STARTER_CONFIG
from src.generator import generate_master_data
from src.workflow import generate_dependent_records
from src.anomalies import inject_anomalies
from src.validators import validate_data


def build_baseline():
    master = generate_master_data(STARTER_CONFIG)
    dependent = generate_dependent_records(master, STARTER_CONFIG)
    return {**master, **dependent}


def test_baseline_data_has_no_validation_issues():
    data = build_baseline()

    assert validate_data(data) == []


def test_anomaly_injection_returns_five_labels():
    baseline = build_baseline()
    _, labels = inject_anomalies(baseline)

    assert len(labels) == 5


def test_all_injected_anomaly_types_are_detected():
    baseline = build_baseline()
    anomalous_data, labels = inject_anomalies(baseline)

    expected_types = {label["issue_type"] for label in labels}
    detected_types = {
        issue["issue_type"] for issue in validate_data(anomalous_data)
    }

    assert expected_types <= detected_types


def test_anomaly_injection_does_not_mutate_baseline():
    baseline = build_baseline()
    original = deepcopy(baseline)

    inject_anomalies(baseline)

    assert baseline == original