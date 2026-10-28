
"""Inject labelled anomalies into copies of synthetic workflow records."""

from copy import deepcopy
from typing import Any


def inject_anomalies(
    baseline: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    """Return anomalous data and separate ground-truth labels."""
    data = deepcopy(baseline)
    labels: list[dict[str, Any]] = []

    def label(issue_type: str, entity_type: str, entity_id: str, expected: str) -> None:
        labels.append({
            "issue_type": issue_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "expected_detection": expected,
        })

    employees = data["employees"]
    grants = data["access_grants"]
    assets = data["assets"]
    tasks = data["tasks"]
    dependencies = data["task_dependencies"]

    # 1. Access granted before the employee start date.
    employee = next(
        (e for e in employees if e["employment_status"] == "active"),
        None,
    )
    if employee is not None:
        grants.append({
            "grant_id": f"GRANT-{employee['employee_id']}-ANOM-001",
            "employee_id": employee["employee_id"],
            "access_role_id": "AR-001",
            "granted_at": "2025-01-01T09:00:00+00:00",
            "approved_at": None,
            "revoked_at": None,
            "grant_status": "active",
        })
        label(
            "ACCESS_BEFORE_START_OR_APPROVAL",
            "AccessGrant",
            f"GRANT-{employee['employee_id']}-ANOM-001",
            "Flag grant because approval is missing and grant predates employment start",
        )

    # 2. Duplicate assignment: copy an asset assignment to another employee.
    assigned_asset = next(
        (a for a in assets if a["assigned_employee_id"] is not None),
        None,
    )
    other_employee = next(
        (
            e for e in employees
            if assigned_asset is not None
            and e["employee_id"] != assigned_asset["assigned_employee_id"]
            and e["employment_status"] == "active"
        ),
        None,
    )
    if assigned_asset is not None and other_employee is not None:
        asset_id = assigned_asset["asset_id"]
        assets.append({
            **assigned_asset,
            "asset_id": f"{asset_id}-DUP",
            "serial_number": assigned_asset["serial_number"],
            "assigned_employee_id": other_employee["employee_id"],
        })
        label(
            "DUPLICATE_ASSET_ASSIGNMENT",
            "Asset",
            f"{asset_id}-DUP",
            "Flag asset as a duplicate assignment of the same physical equipment",
        )

    # 3. Terminated employee retains an active grant.
    terminated = next(
        (e for e in employees if e["employment_status"] == "terminated"),
        None,
    )
    if terminated is not None:
        grant_id = f"GRANT-{terminated['employee_id']}-ANOM-002"
        grants.append({
            "grant_id": grant_id,
            "employee_id": terminated["employee_id"],
            "access_role_id": "AR-001",
            "granted_at": "2026-01-01T09:00:00+00:00",
            "approved_at": "2026-01-01T08:00:00+00:00",
            "revoked_at": None,
            "grant_status": "active",
        })
        label(
            "TERMINATED_EMPLOYEE_ACTIVE_GRANT",
            "AccessGrant",
            grant_id,
            "Flag active access assigned to a terminated employee",
        )

    # 4. Create a cycle using two existing onboarding tasks.
    onboarding_tasks = [
        t for t in tasks
        if t["case_type"] == "onboarding"
    ]
    if len(onboarding_tasks) >= 2:
        first = onboarding_tasks[0]
        second = onboarding_tasks[1]
        dependencies.extend([
            {
                "dependency_id": "DEP-ANOM-CYCLE-001",
                "task_id": first["task_id"],
                "prerequisite_task_id": second["task_id"],
            },
            {
                "dependency_id": "DEP-ANOM-CYCLE-002",
                "task_id": second["task_id"],
                "prerequisite_task_id": first["task_id"],
            },
        ])
        label(
            "TASK_DEPENDENCY_CYCLE",
            "Dependency",
            "DEP-ANOM-CYCLE-001",
            "Flag cycle among the two linked tasks",
        )

    # 5. Mark an assigned asset as recovered but leave its assignment intact.
    assigned_asset = next(
        (a for a in assets if a["assigned_employee_id"] is not None),
        None,
    )
    if assigned_asset is not None:
        assigned_asset["asset_status"] = "recovered"
        assigned_asset["recovered_at"] = "2026-10-01T12:00:00+00:00"
        label(
            "RECOVERED_ASSET_STILL_ASSIGNED",
            "Asset",
            assigned_asset["asset_id"],
            "Flag recovered asset that still references an assigned employee",
        )

    return data, labels
