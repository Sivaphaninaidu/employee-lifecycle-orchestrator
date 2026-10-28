
"""Generate reproducible synthetic master data for the lifecycle system."""

import random
from datetime import date, timedelta

from src.config import DatasetConfig


DEPARTMENTS = [
    ("DEPT-001", "Engineering", "CC-100"),
    ("DEPT-002", "Human Resources", "CC-200"),
    ("DEPT-003", "IT Operations", "CC-300"),
    ("DEPT-004", "Facilities", "CC-400"),
]

ROLE_TEMPLATES = [
    ("ROLE-001", "Software Engineer", "DEPT-001", "employee"),
    ("ROLE-002", "Data Analyst", "DEPT-001", "employee"),
    ("ROLE-003", "HR Partner", "DEPT-002", "employee"),
    ("ROLE-004", "IT Support Engineer", "DEPT-003", "employee"),
    ("ROLE-005", "Facilities Coordinator", "DEPT-004", "employee"),
    ("ROLE-006", "Contract Developer", "DEPT-001", "contractor"),
]

FIRST_NAMES = [
    "Aarav", "Ananya", "Arjun", "Diya", "Ishaan",
    "Kavya", "Meera", "Neel", "Riya", "Vihaan",
]
LAST_NAMES = [
    "Sharma", "Reddy", "Patel", "Rao", "Gupta",
    "Kumar", "Iyer", "Das", "Nair", "Singh",
]


def _random_date(rng: random.Random, start: date, days: int) -> date:
    return start + timedelta(days=rng.randint(0, days))


def generate_master_data(config: DatasetConfig) -> dict[str, list[dict]]:
    """Create deterministic departments, roles, managers and employees."""
    config.validate()
    rng = random.Random(config.seed)

    departments = [
        {
            "department_id": dept_id,
            "department_name": name,
            "cost_center": cost_center,
        }
        for dept_id, name, cost_center in DEPARTMENTS
    ]

    roles = [
        {
            "role_id": role_id,
            "role_name": name,
            "department_id": dept_id,
            "employment_type": employment_type,
            "effective_from": "2026-01-01",
            "effective_to": None,
        }
        for role_id, name, dept_id, employment_type in ROLE_TEMPLATES
    ]

    managers = []
    manager_by_department = {}

    for index, department in enumerate(departments, start=1):
        manager_id = f"MGR-{index:04d}"
        manager_by_department[department["department_id"]] = manager_id
        managers.append({
            "manager_id": manager_id,
            "manager_name": f"Manager {index}",
            "department_id": department["department_id"],
            "email": f"manager{index}@example.test",
            "active": 1,
        })

    employees = []
    base_date = date(2026, 1, 1)

    for index in range(1, config.employees + 1):
        employee_id = f"EMP-{index:06d}"
        role = roles[(index - 1) % len(roles)]
        start_date = _random_date(rng, base_date, 364)

        # Some hires have delayed starts; keep the planned start date as
        # the employee's authoritative start date for this initial stage.
        if index % 20 == 0:
            start_date += timedelta(days=14)

        employment_status = "active"
        end_date = None

        # Deterministic contractor and exit coverage.
        if index % 25 == 0:
            employment_status = "terminated"
            end_date = (start_date + timedelta(days=90)).isoformat()

        employees.append({
            "employee_id": employee_id,
            "full_name": (
                f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)} {index}"
            ),
            "email": f"employee{index}@example.test",
            "role_id": role["role_id"],
            "department_id": role["department_id"],
            "manager_id": manager_by_department[role["department_id"]],
            "employment_type": role["employment_type"],
            "employment_status": employment_status,
            "start_date": start_date.isoformat(),
            "end_date": end_date,
        })

    return {
        "departments": departments,
        "roles": roles,
        "managers": managers,
        "employees": employees,
    }
