from src.config import STARTER_CONFIG
from src.generator import generate_master_data
from src.workflow import generate_dependent_records


def build_data():
    master = generate_master_data(STARTER_CONFIG)
    dependent = generate_dependent_records(master, STARTER_CONFIG)
    return master, dependent


def test_workflow_generates_configured_task_count():
    _, dependent = build_data()

    assert len(dependent["tasks"]) == STARTER_CONFIG.tasks


def test_workflow_generates_configured_grant_count():
    _, dependent = build_data()

    assert len(dependent["access_grants"]) == STARTER_CONFIG.access_grants


def test_workflow_generates_configured_asset_count():
    _, dependent = build_data()

    assert len(dependent["assets"]) == STARTER_CONFIG.assets


def test_all_tasks_reference_existing_cases():
    master, dependent = build_data()

    onboarding_ids = {
        case["onboarding_case_id"]
        for case in dependent["onboarding_cases"]
    }
    offboarding_ids = {
        case["offboarding_case_id"]
        for case in dependent["offboarding_cases"]
    }

    for task in dependent["tasks"]:
        if task["case_type"] == "onboarding":
            assert task["case_id"] in onboarding_ids
        elif task["case_type"] == "offboarding":
            assert task["case_id"] in offboarding_ids
        else:
            raise AssertionError(
                f"Unexpected task case type: {task['case_type']}"
            )


def test_access_grants_reference_existing_employees_and_roles():
    master, dependent = build_data()

    employee_ids = {employee["employee_id"] for employee in master["employees"]}
    access_role_ids = {
        role["access_role_id"] for role in dependent["access_roles"]
    }

    for grant in dependent["access_grants"]:
        assert grant["employee_id"] in employee_ids
        assert grant["access_role_id"] in access_role_ids