from src.config import STARTER_CONFIG
from src.generator import generate_master_data


def test_master_data_has_required_entities():
    data = generate_master_data(STARTER_CONFIG)

    assert "departments" in data
    assert "roles" in data
    assert "managers" in data
    assert "employees" in data


def test_master_data_counts():
    data = generate_master_data(STARTER_CONFIG)

    assert len(data["departments"]) == 4
    assert len(data["roles"]) == 6
    assert len(data["managers"]) == 4
    assert len(data["employees"]) == STARTER_CONFIG.employees


def test_employee_ids_are_unique():
    data = generate_master_data(STARTER_CONFIG)

    employee_ids = [employee["employee_id"] for employee in data["employees"]]

    assert len(employee_ids) == len(set(employee_ids))


def test_same_seed_generates_same_master_data():
    first = generate_master_data(STARTER_CONFIG)
    second = generate_master_data(STARTER_CONFIG)

    assert first == second