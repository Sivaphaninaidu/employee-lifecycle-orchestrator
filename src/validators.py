
"""Independent validation rules for employee lifecycle data."""

from collections import Counter, defaultdict
from datetime import date, datetime
from typing import Any


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _has_duplicates(values: list[str]) -> set[str]:
    counts = Counter(values)
    return {value for value, count in counts.items() if count > 1}


def validate_data(
    data: dict[str, list[dict[str, Any]]],
) -> list[dict[str, str]]:
    """Detect integrity and lifecycle violations without using ground truth."""
    issues: list[dict[str, str]] = []

    def report(issue_type: str, entity_type: str, entity_id: str, message: str) -> None:
        issues.append({
            "issue_type": issue_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "message": message,
        })

    employees = data.get("employees", [])
    roles = data.get("roles", [])
    departments = data.get("departments", [])
    managers = data.get("managers", [])
    onboarding = data.get("onboarding_cases", [])
    offboarding = data.get("offboarding_cases", [])
    tasks = data.get("tasks", [])
    dependencies = data.get("task_dependencies", [])
    access_roles = data.get("access_roles", [])
    grants = data.get("access_grants", [])
    assets = data.get("assets", [])

    # 1. Primary key uniqueness.
    key_fields = {
        "Department": (departments, "department_id"),
        "Role": (roles, "role_id"),
        "Manager": (managers, "manager_id"),
        "Employee": (employees, "employee_id"),
        "OnboardingCase": (onboarding, "onboarding_case_id"),
        "OffboardingCase": (offboarding, "offboarding_case_id"),
        "Task": (tasks, "task_id"),
        "AccessRole": (access_roles, "access_role_id"),
        "AccessGrant": (grants, "grant_id"),
        "Asset": (assets, "asset_id"),
    }
    for entity_type, (rows, field) in key_fields.items():
        duplicates = _has_duplicates([str(row.get(field)) for row in rows])
        for duplicate in duplicates:
            report("DUPLICATE_PRIMARY_KEY", entity_type, duplicate,
                   f"Duplicate primary key value in {field}")

    # 2. Referential integrity for core relationships.
    employee_ids = {e["employee_id"] for e in employees}
    department_ids = {d["department_id"] for d in departments}
    role_ids = {r["role_id"] for r in roles}
    manager_ids = {m["manager_id"] for m in managers}
    access_role_ids = {r["access_role_id"] for r in access_roles}
    task_ids = {t["task_id"] for t in tasks}
    onboarding_ids = {c["onboarding_case_id"] for c in onboarding}
    offboarding_ids = {c["offboarding_case_id"] for c in offboarding}

    for employee in employees:
        eid = employee["employee_id"]
        if employee.get("role_id") not in role_ids:
            report("INVALID_FOREIGN_KEY", "Employee", eid, "Unknown role_id")
        if employee.get("department_id") not in department_ids:
            report("INVALID_FOREIGN_KEY", "Employee", eid, "Unknown department_id")
        if employee.get("manager_id") and employee["manager_id"] not in manager_ids:
            report("INVALID_FOREIGN_KEY", "Employee", eid, "Unknown manager_id")

    for role in roles:
        if role.get("department_id") not in department_ids:
            report("INVALID_FOREIGN_KEY", "Role", role["role_id"],
                   "Unknown department_id")

    for case in onboarding:
        if case.get("employee_id") not in employee_ids:
            report("INVALID_FOREIGN_KEY", "OnboardingCase",
                   case["onboarding_case_id"], "Unknown employee_id")

    for case in offboarding:
        if case.get("employee_id") not in employee_ids:
            report("INVALID_FOREIGN_KEY", "OffboardingCase",
                   case["offboarding_case_id"], "Unknown employee_id")

    # 3. Task case references and dependency graph.
    graph: dict[str, list[str]] = defaultdict(list)
    for task in tasks:
        if task["case_type"] == "onboarding" and task["case_id"] not in onboarding_ids:
            report("INVALID_TASK_CASE", "Task", task["task_id"],
                   "Unknown onboarding case")
        elif task["case_type"] == "offboarding" and task["case_id"] not in offboarding_ids:
            report("INVALID_TASK_CASE", "Task", task["task_id"],
                   "Unknown offboarding case")

        if task["task_status"] == "completed" and not task.get("completed_at"):
            report("COMPLETED_TASK_WITHOUT_TIMESTAMP", "Task", task["task_id"],
                   "Completed task has no completed_at timestamp")

    for dependency in dependencies:
        task_id = dependency["task_id"]
        prerequisite_id = dependency["prerequisite_task_id"]
        if task_id not in task_ids or prerequisite_id not in task_ids:
            report("INVALID_DEPENDENCY_REFERENCE", "Dependency",
                   dependency["dependency_id"], "Unknown task reference")
        else:
            graph[task_id].append(prerequisite_id)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            report("TASK_DEPENDENCY_CYCLE", "Task", task_id,
                   "Dependency graph contains a cycle")
            return
        if task_id in visited:
            return

        visiting.add(task_id)
        for prerequisite_id in graph.get(task_id, []):
            visit(prerequisite_id)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in task_ids:
        if task_id not in visited:
            visit(task_id)

    # 4. Access lifecycle checks.
    employee_by_id = {e["employee_id"]: e for e in employees}
    for grant in grants:
        gid = grant["grant_id"]
        employee = employee_by_id.get(grant["employee_id"])

        if employee is None:
            report("INVALID_GRANT_EMPLOYEE", "AccessGrant", gid,
                   "Unknown employee reference")
            continue
        if grant["access_role_id"] not in access_role_ids:
            report("INVALID_GRANT_ROLE", "AccessGrant", gid,
                   "Unknown access role reference")

        granted_at = _parse_datetime(grant.get("granted_at"))
        approved_at = _parse_datetime(grant.get("approved_at"))
        start_date = date.fromisoformat(employee["start_date"])

        if grant["grant_status"] == "active":
            if employee["employment_status"] == "terminated":
                report("TERMINATED_EMPLOYEE_ACTIVE_GRANT", "AccessGrant", gid,
                       "Terminated employee still has active access")
            if granted_at and granted_at.date() < start_date:
                report("ACCESS_BEFORE_START_OR_APPROVAL", "AccessGrant", gid,
                       "Grant predates employee start date")
            if approved_at is None:
                report("ACCESS_BEFORE_START_OR_APPROVAL", "AccessGrant", gid,
                       "Active grant has no approval timestamp")
            elif granted_at and approved_at > granted_at:
                report("ACCESS_BEFORE_START_OR_APPROVAL", "AccessGrant", gid,
                       "Grant predates its approval")

        if grant["grant_status"] == "revoked" and not grant.get("revoked_at"):
            report("REVOKED_GRANT_WITHOUT_TIMESTAMP", "AccessGrant", gid,
                   "Revoked grant has no revoked_at timestamp")

    # 5. Asset reconciliation.
    assigned_employee_counts = Counter(
        a["assigned_employee_id"]
        for a in assets
        if a.get("asset_status") == "assigned"
        and a.get("assigned_employee_id")
    )

    for asset in assets:
        aid = asset["asset_id"]
        assigned_employee_id = asset.get("assigned_employee_id")

        if assigned_employee_id and assigned_employee_id not in employee_ids:
            report("INVALID_ASSET_EMPLOYEE", "Asset", aid,
                   "Unknown employee reference")

        if asset.get("asset_status") == "recovered" and assigned_employee_id:
            report("RECOVERED_ASSET_STILL_ASSIGNED", "Asset", aid,
                   "Recovered asset still has an employee assignment")

        if asset.get("asset_status") == "assigned" and assigned_employee_id:
            if assigned_employee_counts[assigned_employee_id] > 1:
                report("DUPLICATE_ASSET_ASSIGNMENT", "Asset", aid,
                       "Employee has multiple assigned asset records")

    # Duplicate physical serial numbers indicate duplicate asset records.
    serial_counts = Counter(
        a.get("serial_number") for a in assets if a.get("serial_number")
    )
    for asset in assets:
        if serial_counts.get(asset.get("serial_number"), 0) > 1:
            report("DUPLICATE_ASSET_ASSIGNMENT", "Asset", asset["asset_id"],
                   "Serial number appears on multiple asset records")

    return issues
