
"""Entity definitions and relationship metadata for the lifecycle system."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FieldDefinition:
    name: str
    data_type: str
    required: bool
    allowed_values: tuple[str, ...] = ()
    unique: bool = False
    foreign_key: str | None = None
    validation_rule: str = ""


@dataclass(frozen=True)
class EntityDefinition:
    name: str
    primary_key: str
    fields: tuple[FieldDefinition, ...]
    description: str


ENTITIES: dict[str, EntityDefinition] = {
    "Department": EntityDefinition(
        name="Department",
        primary_key="department_id",
        description="Organization department master data",
        fields=(
            FieldDefinition("department_id", "str", True, unique=True),
            FieldDefinition("department_name", "str", True, unique=True),
            FieldDefinition("cost_center", "str", True, unique=True),
        ),
    ),
    "Role": EntityDefinition(
        name="Role",
        primary_key="role_id",
        description="Job roles and role templates",
        fields=(
            FieldDefinition("role_id", "str", True, unique=True),
            FieldDefinition("role_name", "str", True, unique=True),
            FieldDefinition("department_id", "str", True, foreign_key="Department.department_id"),
            FieldDefinition("employment_type", "str", True,
                            ("employee", "contractor")),
            FieldDefinition("effective_from", "date", True),
            FieldDefinition("effective_to", "date", False),
        ),
    ),
    "Manager": EntityDefinition(
        name="Manager",
        primary_key="manager_id",
        description="Manager directory",
        fields=(
            FieldDefinition("manager_id", "str", True, unique=True),
            FieldDefinition("manager_name", "str", True),
            FieldDefinition("department_id", "str", True, foreign_key="Department.department_id"),
            FieldDefinition("email", "str", True, unique=True),
            FieldDefinition("active", "bool", True),
        ),
    ),
    "Employee": EntityDefinition(
        name="Employee",
        primary_key="employee_id",
        description="Employee and contractor master records",
        fields=(
            FieldDefinition("employee_id", "str", True, unique=True),
            FieldDefinition("full_name", "str", True),
            FieldDefinition("email", "str", True, unique=True),
            FieldDefinition("role_id", "str", True, foreign_key="Role.role_id"),
            FieldDefinition("department_id", "str", True, foreign_key="Department.department_id"),
            FieldDefinition("manager_id", "str", False, foreign_key="Manager.manager_id"),
            FieldDefinition("employment_type", "str", True,
                            ("employee", "contractor")),
            FieldDefinition("employment_status", "str", True,
                            ("preboarding", "active", "on_leave", "terminated")),
            FieldDefinition("start_date", "date", True),
            FieldDefinition("end_date", "date", False),
        ),
    ),
    "OnboardingCase": EntityDefinition(
        name="OnboardingCase",
        primary_key="onboarding_case_id",
        description="One onboarding case per hire",
        fields=(
            FieldDefinition("onboarding_case_id", "str", True, unique=True),
            FieldDefinition("employee_id", "str", True, unique=True,
                            foreign_key="Employee.employee_id"),
            FieldDefinition("created_at", "datetime", True),
            FieldDefinition("planned_start_date", "date", True),
            FieldDefinition("case_status", "str", True,
                            ("open", "in_progress", "completed", "cancelled")),
        ),
    ),
    "Task": EntityDefinition(
        name="Task",
        primary_key="task_id",
        description="Onboarding and offboarding work items",
        fields=(
            FieldDefinition("task_id", "str", True, unique=True),
            FieldDefinition("case_type", "str", True, ("onboarding", "offboarding")),
            FieldDefinition("case_id", "str", True,
                            validation_rule="Must reference a case of case_type"),
            FieldDefinition("task_name", "str", True),
            FieldDefinition("owner_team", "str", True,
                            ("HR", "IT", "Facilities", "Manager")),
            FieldDefinition("task_status", "str", True,
                            ("blocked", "pending", "in_progress", "completed", "cancelled")),
            FieldDefinition("due_date", "date", True),
            FieldDefinition("completed_at", "datetime", False),
        ),
    ),
    "Dependency": EntityDefinition(
        name="Dependency",
        primary_key="dependency_id",
        description="Directed prerequisite relationship between tasks",
        fields=(
            FieldDefinition("dependency_id", "str", True, unique=True),
            FieldDefinition("task_id", "str", True, foreign_key="Task.task_id"),
            FieldDefinition("prerequisite_task_id", "str", True,
                            foreign_key="Task.task_id"),
        ),
    ),
    "AccessRole": EntityDefinition(
        name="AccessRole",
        primary_key="access_role_id",
        description="Access templates associated with job roles",
        fields=(
            FieldDefinition("access_role_id", "str", True, unique=True),
            FieldDefinition("access_role_name", "str", True, unique=True),
            FieldDefinition("system_name", "str", True),
            FieldDefinition("risk_level", "str", True,
                            ("low", "medium", "high", "critical")),
        ),
    ),
    "AccessGrant": EntityDefinition(
        name="AccessGrant",
        primary_key="grant_id",
        description="Access assignment and revocation history",
        fields=(
            FieldDefinition("grant_id", "str", True, unique=True),
            FieldDefinition("employee_id", "str", True, foreign_key="Employee.employee_id"),
            FieldDefinition("access_role_id", "str", True,
                            foreign_key="AccessRole.access_role_id"),
            FieldDefinition("granted_at", "datetime", True),
            FieldDefinition("approved_at", "datetime", False),
            FieldDefinition("revoked_at", "datetime", False),
            FieldDefinition("grant_status", "str", True,
                            ("pending", "active", "revoked", "rejected")),
        ),
    ),
    "Asset": EntityDefinition(
        name="Asset",
        primary_key="asset_id",
        description="Equipment inventory and current assignment",
        fields=(
            FieldDefinition("asset_id", "str", True, unique=True),
            FieldDefinition("asset_type", "str", True,
                            ("laptop", "monitor", "phone", "access_card", "other")),
            FieldDefinition("serial_number", "str", True, unique=True),
            FieldDefinition("asset_status", "str", True,
                            ("available", "assigned", "recovered", "retired")),
            FieldDefinition("assigned_employee_id", "str", False,
                            foreign_key="Employee.employee_id"),
            FieldDefinition("assigned_at", "datetime", False),
            FieldDefinition("recovered_at", "datetime", False),
        ),
    ),
    "OffboardingCase": EntityDefinition(
        name="OffboardingCase",
        primary_key="offboarding_case_id",
        description="Employee exit, access revocation and equipment recovery",
        fields=(
            FieldDefinition("offboarding_case_id", "str", True, unique=True),
            FieldDefinition("employee_id", "str", True, unique=True,
                            foreign_key="Employee.employee_id"),
            FieldDefinition("termination_date", "date", True),
            FieldDefinition("reason", "str", True,
                            ("resignation", "contract_end", "termination", "retirement")),
            FieldDefinition("case_status", "str", True,
                            ("open", "in_progress", "completed")),
        ),
    ),
    "AuditEvent": EntityDefinition(
        name="AuditEvent",
        primary_key="audit_event_id",
        description="Append-only record of business state changes and overrides",
        fields=(
            FieldDefinition("audit_event_id", "str", True, unique=True),
            FieldDefinition("entity_type", "str", True),
            FieldDefinition("entity_id", "str", True),
            FieldDefinition("event_type", "str", True),
            FieldDefinition("event_time", "datetime", True),
            FieldDefinition("actor", "str", True),
            FieldDefinition("details_json", "json", True),
            FieldDefinition("issue_type", "str", False),
        ),
    ),
}


def validate_schema_definitions() -> list[str]:
    """Check schema metadata for basic structural problems."""
    errors: list[str] = []

    for entity_name, entity in ENTITIES.items():
        field_names = [field.name for field in entity.fields]

        if entity_name != entity.name:
            errors.append(f"Entity key mismatch: {entity_name}")

        if entity.primary_key not in field_names:
            errors.append(f"{entity_name}: primary key field is missing")

        if len(field_names) != len(set(field_names)):
            errors.append(f"{entity_name}: duplicate field names")

        for field in entity.fields:
            if field.foreign_key:
                parent_entity, separator, parent_field = field.foreign_key.partition(".")
                if not separator or parent_entity not in ENTITIES:
                    errors.append(
                        f"{entity_name}.{field.name}: invalid foreign key target"
                    )
                elif parent_field != ENTITIES[parent_entity].primary_key:
                    errors.append(
                        f"{entity_name}.{field.name}: target must reference "
                        f"{parent_entity}'s primary key"
                    )

    return errors
