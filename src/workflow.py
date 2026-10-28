"""Generate dependent employee lifecycle records."""
from datetime import date, datetime, timedelta, timezone
from src.config import DatasetConfig
TASK_TEMPLATES = [
    ("Confirm employment details", "HR", []),
    ("Manager approval", "Manager", ["Confirm employment details"]),
    ("Prepare workstation", "Facilities", ["Manager approval"]),
    ("Provision system access", "IT", ["Manager approval"]),
    ("Confirm equipment receipt", "Facilities", ["Prepare workstation"]),
]
ACCESS_ROLE_TEMPLATES = [
    ("AR-001", "Email User", "Email", "low"),
    ("AR-002", "Engineering Repository", "Source Control", "medium"),
    ("AR-003", "HR Records", "HR System", "high"),
    ("AR-004", "IT Administrator", "IT Platform", "critical"),
]
def _now_text() -> str:
    """Return a fixed UTC timestamp for reproducible synthetic data."""
    return "2026-10-22T12:00:00+00:00"
def generate_dependent_records(
    master: dict[str, list[dict]],
    config: DatasetConfig | None = None,
) -> dict[str, list[dict]]:
    """Build dependent records and pad task count to the configured target."""
    if config is None:
        config = DatasetConfig(
            employees=len(master["employees"]),
            tasks=max(0, len(master["employees"]) * 8),
            access_grants=max(0, len(master["employees"]) * 2),
            assets=max(0, len(master["employees"])),
        )
    config.validate()
    employees = master["employees"]
    onboarding_cases = []
    offboarding_cases = []
    tasks = []
    dependencies = []
    access_roles = [
        {
            "access_role_id": role_id,
            "access_role_name": name,
            "system_name": system,
            "risk_level": risk,
        }
        for role_id, name, system, risk in ACCESS_ROLE_TEMPLATES
    ]
    role_access_roles = []
    access_grants = []
    assets = []
    audit_events = []
    task_counter_by_case = {}
    grant_counter_by_employee = {}
    asset_counter = 0
    dependency_counter = 0
    audit_counter = 0
    # Map each job role to the access templates appropriate for it.
            # Map each job role to the access templates appropriate for it.
    for role in master["roles"]:
        for access_role in access_roles:
            if (
                role["role_name"] == "HR Partner"
                and access_role["access_role_id"] == "AR-003"
            ):
                role_access_roles.append({
                    "role_id": role["role_id"],
                    "access_role_id": access_role["access_role_id"],
                    "effective_from": role["effective_from"],
                    "effective_to": role["effective_to"],
                })
            elif (
                role["role_name"] == "IT Support Engineer"
                and access_role["access_role_id"] == "AR-004"
            ):
                role_access_roles.append({
                    "role_id": role["role_id"],
                    "access_role_id": access_role["access_role_id"],
                    "effective_from": role["effective_from"],
                    "effective_to": role["effective_to"],
                })
            elif (
                role["department_id"] == "DEPT-001"
                and access_role["access_role_id"] == "AR-002"
            ):
                role_access_roles.append({
                    "role_id": role["role_id"],
                    "access_role_id": access_role["access_role_id"],
                    "effective_from": role["effective_from"],
                    "effective_to": role["effective_to"],
                })
            elif access_role["access_role_id"] == "AR-001":
                role_access_roles.append({
                    "role_id": role["role_id"],
                    "access_role_id": access_role["access_role_id"],
                    "effective_from": role["effective_from"],
                    "effective_to": role["effective_to"],
                })
    for employee in employees:
        employee_id = employee["employee_id"]
        start_date = date.fromisoformat(employee["start_date"])
        employee_number = int(employee_id.split("-")[1])
        onboarding_id = f"ONB-2026-{employee_number:06d}"
        onboarding_cases.append({
            "onboarding_case_id": onboarding_id,
            "employee_id": employee_id,
            "created_at": _now_text(),
            "planned_start_date": start_date.isoformat(),
            "case_status": (
                "completed" if employee["employment_status"] == "active"
                else "in_progress"
            ),
        })
        task_ids_by_name = {}
        task_counter_by_case[onboarding_id] = 0
        for task_name, owner_team, prerequisite_names in TASK_TEMPLATES:
            task_counter_by_case[onboarding_id] += 1
            task_id = (
                f"TASK-{onboarding_id}-"
                f"{task_counter_by_case[onboarding_id]:03d}"
            )
            prerequisite_ids = [
                task_ids_by_name[name] for name in prerequisite_names
            ]
            status = "pending" if not prerequisite_ids else "blocked"
            tasks.append({
                "task_id": task_id,
                "case_type": "onboarding",
                "case_id": onboarding_id,
                "task_name": task_name,
                "owner_team": owner_team,
                "task_status": status,
                "due_date": (start_date - timedelta(days=2)).isoformat(),
                "completed_at": None,
            })
            task_ids_by_name[task_name] = task_id
            for prerequisite_id in prerequisite_ids:
                dependency_counter += 1
                dependencies.append({
                    "dependency_id": f"DEP-{dependency_counter:07d}",
                    "task_id": task_id,
                    "prerequisite_task_id": prerequisite_id,
                })
                # Baseline access for active employees is approved on/after start date.
        if employee["employment_status"] == "active":
            grant_counter_by_employee[employee_id] = 1

            approval_time = datetime.combine(
                start_date, datetime.min.time(), tzinfo=timezone.utc
            ).isoformat()

            access_grants.append({
                "grant_id": f"GRANT-{employee_id}-001",
                "employee_id": employee_id,
                "access_role_id": "AR-001",
                "granted_at": approval_time,
                "approved_at": approval_time,
                "revoked_at": None,
                "grant_status": "active",
            })
        # Assign a baseline laptop to every fifth active employee.
        if (
            employee["employment_status"] == "active"
            and employee_number % 5 == 0
            and len(assets) < config.assets
        ):
            asset_counter += 1
            assets.append({
                "asset_id": f"AST-{asset_counter:06d}",
                "asset_type": "laptop",
                "serial_number": f"SYN-LAP-{asset_counter:06d}",
                "asset_status": "assigned",
                "assigned_employee_id": employee_id,
                "assigned_at": _now_text(),
                "recovered_at": None,
            })
        if employee["employment_status"] == "terminated":
            offboarding_id = f"OFF-2026-{employee_number:06d}"
            offboarding_cases.append({
                "offboarding_case_id": offboarding_id,
                "employee_id": employee_id,
                "termination_date": employee["end_date"],
                "reason": (
                    "contract_end"
                    if employee["employment_type"] == "contractor"
                    else "resignation"
                ),
                "case_status": "open",
            })
            for task_name, owner_team in [
                ("Revoke system access", "IT"),
                ("Recover equipment", "Facilities"),
                ("Confirm exit checklist", "HR"),
            ]:
                task_counter_by_case[offboarding_id] = (
                    task_counter_by_case.get(offboarding_id, 0) + 1
                )
                task_id = (
                    f"TASK-{offboarding_id}-"
                    f"{task_counter_by_case[offboarding_id]:03d}"
                )
                tasks.append({
                    "task_id": task_id,
                    "case_type": "offboarding",
                    "case_id": offboarding_id,
                    "task_name": task_name,
                    "owner_team": owner_team,
                    "task_status": "pending",
                    "due_date": employee["end_date"],
                    "completed_at": None,
                })
        audit_counter += 1
        audit_events.append({
            "audit_event_id": f"AUD-{audit_counter:07d}",
            "entity_type": "Employee",
            "entity_id": employee_id,
            "event_type": "SYNTHETIC_RECORD_CREATED",
            "event_time": _now_text(),
            "actor": "synthetic_generator",
            "details_json": '{"source":"generator","version":1}',
            "issue_type": None,
        })

        # Add approved grants until the configured target is reached.
    active_employees = [
        employee for employee in employees
        if employee["employment_status"] == "active"
    ]

    if len(access_grants) > config.access_grants:
        raise ValueError(
            f"Generated {len(access_grants)} baseline grants, exceeding "
            f"configured target of {config.access_grants}"
        )

    if not active_employees and len(access_grants) < config.access_grants:
        raise ValueError("Cannot create access grants without active employees.")

    extra_grant_index = 0
    extra_access_role_ids = ["AR-002", "AR-003", "AR-004"]

    while len(access_grants) < config.access_grants:
        employee = active_employees[
            extra_grant_index % len(active_employees)
        ]
        employee_id = employee["employee_id"]
        employee_start = date.fromisoformat(employee["start_date"])
        grant_number = grant_counter_by_employee.get(employee_id, 1) + 1
        grant_counter_by_employee[employee_id] = grant_number

        approval_time = datetime.combine(
            employee_start, datetime.min.time(), tzinfo=timezone.utc
        ).isoformat()

        access_role_id = extra_access_role_ids[
            extra_grant_index % len(extra_access_role_ids)
        ]

        access_grants.append({
            "grant_id": f"GRANT-{employee_id}-{grant_number:03d}",
            "employee_id": employee_id,
            "access_role_id": access_role_id,
            "granted_at": approval_time,
            "approved_at": approval_time,
            "revoked_at": None,
            "grant_status": "active",
        })

        extra_grant_index += 1 
    # Add approved grants until the configured target is reached.
    active_employees = [
        employee for employee in employees
        if employee["employment_status"] == "active"
    ]

    if len(access_grants) > config.access_grants:
        raise ValueError("Baseline grants exceed the configured target.")

    if not active_employees and len(access_grants) < config.access_grants:
        raise ValueError("Cannot create extra grants without active employees.")

    extra_grant_index = 0
    extra_access_role_ids = ["AR-002", "AR-003", "AR-004"]

    while len(access_grants) < config.access_grants:
        employee = active_employees[
            extra_grant_index % len(active_employees)
        ]
        employee_id = employee["employee_id"]
        employee_start = date.fromisoformat(employee["start_date"])

        grant_number = grant_counter_by_employee.get(employee_id, 1) + 1
        grant_counter_by_employee[employee_id] = grant_number

        approval_time = datetime.combine(
            employee_start, datetime.min.time(), tzinfo=timezone.utc
        ).isoformat()

        access_role_id = extra_access_role_ids[
            extra_grant_index % len(extra_access_role_ids)
        ]

        access_grants.append({
            "grant_id": f"GRANT-{employee_id}-{grant_number:03d}",
            "employee_id": employee_id,
            "access_role_id": access_role_id,
            "granted_at": approval_time,
            "approved_at": approval_time,
            "revoked_at": None,
            "grant_status": "active",
        })

        extra_grant_index += 1 

        # Add available inventory assets until the configured target is reached.
    while len(assets) < config.assets:
        asset_counter += 1
        assets.append({
            "asset_id": f"AST-{asset_counter:06d}",
            "asset_type": "laptop",
            "serial_number": f"SYN-LAP-{asset_counter:06d}",
            "asset_status": "available",
            "assigned_employee_id": None,
            "assigned_at": None,
            "recovered_at": None,
        })          
    # Add extra independent tasks until the configured total is reached.
    extra_task_templates = [
        ("Complete security training", "IT"),
        ("Acknowledge company policies", "HR"),
        ("Complete data protection training", "IT"),
        ("Review team documentation", "Manager"),
        ("Confirm emergency contact details", "HR"),
    ]
    if len(tasks) > config.tasks:
        raise ValueError(
            f"Generated {len(tasks)} base tasks, exceeding "
            f"configured target of {config.tasks}"
        )
    onboarding_by_id = {
        case["onboarding_case_id"]: case for case in onboarding_cases
    }
    onboarding_ids = list(onboarding_by_id)
    extra_index = 0
    while len(tasks) < config.tasks:
        if not onboarding_ids:
            raise ValueError("Cannot add tasks without onboarding cases.")
        onboarding_id = onboarding_ids[extra_index % len(onboarding_ids)]
        task_number = task_counter_by_case[onboarding_id] + 1
        task_counter_by_case[onboarding_id] = task_number
        task_name, owner_team = extra_task_templates[
            extra_index % len(extra_task_templates)
        ]
        tasks.append({
            "task_id": f"TASK-{onboarding_id}-{task_number:03d}",
            "case_type": "onboarding",
            "case_id": onboarding_id,
            "task_name": task_name,
            "owner_team": owner_team,
            "task_status": "pending",
            "due_date": onboarding_by_id[onboarding_id]["planned_start_date"],
            "completed_at": None,
        })
        extra_index += 1
    return {
        "onboarding_cases": onboarding_cases,
        "offboarding_cases": offboarding_cases,
        "tasks": tasks,
        "task_dependencies": dependencies,
        "access_roles": access_roles,
        "role_access_roles": role_access_roles,
         "access_grants": access_grants,
        "assets": assets,
        "audit_events": audit_events,
    }