
"""SQLite database schema for the employee lifecycle orchestrator."""

import sqlite3
from pathlib import Path


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS departments (
    department_id TEXT PRIMARY KEY,
    department_name TEXT NOT NULL UNIQUE,
    cost_center TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS roles (
    role_id TEXT PRIMARY KEY,
    role_name TEXT NOT NULL UNIQUE,
    department_id TEXT NOT NULL,
    employment_type TEXT NOT NULL
        CHECK (employment_type IN ('employee', 'contractor')),
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

CREATE TABLE IF NOT EXISTS managers (
    manager_id TEXT PRIMARY KEY,
    manager_name TEXT NOT NULL,
    department_id TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    active INTEGER NOT NULL CHECK (active IN (0, 1)),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

CREATE TABLE IF NOT EXISTS employees (
    employee_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role_id TEXT NOT NULL,
    department_id TEXT NOT NULL,
    manager_id TEXT,
    employment_type TEXT NOT NULL
        CHECK (employment_type IN ('employee', 'contractor')),
    employment_status TEXT NOT NULL
        CHECK (employment_status IN
            ('preboarding', 'active', 'on_leave', 'terminated')),
    start_date TEXT NOT NULL,
    end_date TEXT,
    FOREIGN KEY (role_id) REFERENCES roles(role_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (manager_id) REFERENCES managers(manager_id),
    CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE TABLE IF NOT EXISTS onboarding_cases (
    onboarding_case_id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    planned_start_date TEXT NOT NULL,
    case_status TEXT NOT NULL
        CHECK (case_status IN
            ('open', 'in_progress', 'completed', 'cancelled')),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

CREATE TABLE IF NOT EXISTS offboarding_cases (
    offboarding_case_id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL UNIQUE,
    termination_date TEXT NOT NULL,
    reason TEXT NOT NULL
        CHECK (reason IN
            ('resignation', 'contract_end', 'termination', 'retirement')),
    case_status TEXT NOT NULL
        CHECK (case_status IN ('open', 'in_progress', 'completed')),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    case_type TEXT NOT NULL
        CHECK (case_type IN ('onboarding', 'offboarding')),
    case_id TEXT NOT NULL,
    task_name TEXT NOT NULL,
    owner_team TEXT NOT NULL
        CHECK (owner_team IN ('HR', 'IT', 'Facilities', 'Manager')),
    task_status TEXT NOT NULL
        CHECK (task_status IN
            ('blocked', 'pending', 'in_progress', 'completed', 'cancelled')),
    due_date TEXT NOT NULL,
    completed_at TEXT,
    CHECK (task_status != 'completed' OR completed_at IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS task_dependencies (
    dependency_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    prerequisite_task_id TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (prerequisite_task_id) REFERENCES tasks(task_id),
    UNIQUE (task_id, prerequisite_task_id),
    CHECK (task_id != prerequisite_task_id)
);

CREATE TABLE IF NOT EXISTS access_roles (
    access_role_id TEXT PRIMARY KEY,
    access_role_name TEXT NOT NULL UNIQUE,
    system_name TEXT NOT NULL,
    risk_level TEXT NOT NULL
        CHECK (risk_level IN ('low', 'medium', 'high', 'critical'))
);

CREATE TABLE IF NOT EXISTS role_access_roles (
    role_id TEXT NOT NULL,
    access_role_id TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    PRIMARY KEY (role_id, access_role_id, effective_from),
    FOREIGN KEY (role_id) REFERENCES roles(role_id),
    FOREIGN KEY (access_role_id) REFERENCES access_roles(access_role_id),
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

CREATE TABLE IF NOT EXISTS access_grants (
    grant_id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL,
    access_role_id TEXT NOT NULL,
    granted_at TEXT NOT NULL,
    approved_at TEXT,
    revoked_at TEXT,
    grant_status TEXT NOT NULL
        CHECK (grant_status IN ('pending', 'active', 'revoked', 'rejected')),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (access_role_id) REFERENCES access_roles(access_role_id),
    CHECK (grant_status != 'revoked' OR revoked_at IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS assets (
    asset_id TEXT PRIMARY KEY,
    asset_type TEXT NOT NULL
        CHECK (asset_type IN
            ('laptop', 'monitor', 'phone', 'access_card', 'other')),
    serial_number TEXT NOT NULL UNIQUE,
    asset_status TEXT NOT NULL
        CHECK (asset_status IN ('available', 'assigned', 'recovered', 'retired')),
    assigned_employee_id TEXT,
    assigned_at TEXT,
    recovered_at TEXT,
    FOREIGN KEY (assigned_employee_id) REFERENCES employees(employee_id),
    CHECK (asset_status != 'assigned' OR assigned_employee_id IS NOT NULL),
    CHECK (asset_status != 'recovered' OR assigned_employee_id IS NULL)
);

CREATE TABLE IF NOT EXISTS audit_events (
    audit_event_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_time TEXT NOT NULL,
    actor TEXT NOT NULL,
    details_json TEXT NOT NULL,
    issue_type TEXT
);

CREATE INDEX IF NOT EXISTS idx_employees_status
    ON employees(employment_status);
CREATE INDEX IF NOT EXISTS idx_grants_employee_status
    ON access_grants(employee_id, grant_status);
CREATE INDEX IF NOT EXISTS idx_assets_employee
    ON assets(assigned_employee_id);
CREATE INDEX IF NOT EXISTS idx_tasks_case
    ON tasks(case_type, case_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity
    ON audit_events(entity_type, entity_id);
"""


def connect_database(db_path: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection with foreign-key enforcement enabled."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(db_path: str | Path) -> None:
    """Create all tables and indexes if they do not already exist."""
    with connect_database(db_path) as connection:
        connection.executescript(SCHEMA_SQL)


def get_table_names(db_path: str | Path) -> list[str]:
    """Return application table names for verification."""
    with connect_database(db_path) as connection:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

    return [row[0] for row in rows]


def load_dataset(
    db_path: str | Path,
    data: dict[str, list[dict]],
) -> None:
    """Create a fresh database and load generated records in dependency order."""
    import json

    table_mapping = [
        ("departments", "departments"),
        ("roles", "roles"),
        ("managers", "managers"),
        ("employees", "employees"),
        ("onboarding_cases", "onboarding_cases"),
        ("offboarding_cases", "offboarding_cases"),
        ("access_roles", "access_roles"),
        ("role_access_roles", "role_access_roles"),
        ("tasks", "tasks"),
        ("task_dependencies", "task_dependencies"),
        ("access_grants", "access_grants"),
        ("assets", "assets"),
        ("audit_events", "audit_events"),
    ]

    initialize_database(db_path)

    with connect_database(db_path) as connection:
        # Remove prior rows so rerunning the pipeline does not duplicate data.
        for table_name, _ in reversed(table_mapping):
            connection.execute(f"DELETE FROM {table_name}")

        for table_name, data_key in table_mapping:
            records = data.get(data_key, [])
            if not records:
                continue

            for record in records:
                row = dict(record)

                if table_name == "audit_events":
                    details = row.get("details_json", row.get("details", {}))
                    if not isinstance(details, str):
                        row["details_json"] = json.dumps(details, sort_keys=True)
                    else:
                        row["details_json"] = details
                    row.pop("details", None)

                columns = list(row.keys())
                if not columns:
                    continue

                column_sql = ", ".join(f'"{column}"' for column in columns)
                placeholders = ", ".join("?" for _ in columns)
                values = [row[column] for column in columns]

                connection.execute(
                    f"INSERT INTO {table_name} ({column_sql}) "
                    f"VALUES ({placeholders})",
                    values,
                )

