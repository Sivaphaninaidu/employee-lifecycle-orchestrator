
# Data Dictionary — Employee Lifecycle Orchestrator

## 1. Purpose

This document defines the synthetic data model used to orchestrate
employee onboarding, access provisioning, equipment assignment and
offboarding across HR, IT and Facilities.

All records are synthetic. No real employee information is used.

## 2. Entity definitions and relationships

| Entity | Primary key | Relationships | Cardinality |
|---|---|---|---|
| Department | department_id | Department has Roles, Managers and Employees | 1:N |
| Role | role_id | Role belongs to Department | N:1 |
| Manager | manager_id | Manager belongs to Department and manages Employees | N:1 / 1:N |
| Employee | employee_id | Employee belongs to Role and Department; may reference Manager | N:1 |
| OnboardingCase | onboarding_case_id | OnboardingCase references Employee | 1:1 in this dataset |
| Task | task_id | Task belongs to an onboarding or offboarding case | N:1 |
| Dependency | dependency_id | Links a task to its prerequisite task | Task-to-Task N:M |
| AccessRole | access_role_id | Reusable access permission template | N:M with Role |
| AccessGrant | grant_id | Employee receives an AccessRole | N:1 to each |
| Asset | asset_id | Asset may be assigned to an Employee | N:1, optional |
| OffboardingCase | offboarding_case_id | OffboardingCase references Employee | 1:1 in this dataset |
| AuditEvent | audit_event_id | Records a state change for an entity | Polymorphic reference |

## 3. Required ID conventions

| Record | Format |
|---|---|
| Employee | EMP-000001 |
| Onboarding case | ONB-2026-000001 |
| Task | TASK-<case-id>-001 |
| Access grant | GRANT-<employee-id>-001 |
| Asset | AST-000001 |
| Offboarding case | OFF-2026-000001 |

IDs are immutable and generated deterministically.

## 4. Field validation principles

- Primary keys must be unique and non-null.
- Foreign keys must reference existing parent records.
- Dates must be valid ISO dates; timestamps use ISO 8601.
- Optional fields may be null only where the schema allows it.
- Enum values must match the values declared in the schema.
- Effective end dates cannot precede effective start dates.
- Completed tasks require a completion timestamp.
- Active grants require the relevant approvals and employment eligibility.
- Revoked grants require a revocation timestamp.
- An asset marked recovered must not remain actively assigned.
- State changes and overrides must create audit events.

## 5. Lifecycle states

### Employee
preboarding, active, on_leave, terminated

### Onboarding case
open, in_progress, completed, cancelled

### Task
blocked, pending, in_progress, completed, cancelled

### Access grant
pending, active, revoked, rejected

### Asset
available, assigned, recovered, retired

### Offboarding case
open, in_progress, completed

## 6. Data generation and anomaly policy

Generate valid master records before dependent records.
Use a fixed random seed of 20261022.
Derive dates, statuses and metrics from source records and business rules.
Inject known anomalies only after generating valid baseline records.
Keep expected anomaly labels in a separate ground_truth file.
Never use ground-truth labels as input features for detection.

## 7. Known anomalies to test

1. Access granted before the employee start date or approval.
2. The same asset assigned to multiple employees.
3. A terminated employee retains an active access grant.
4. A task dependency cycle exists.
5. A recovered asset remains assigned to an employee.

Each injected anomaly must have a documented issue type, expected detection
and corresponding audit evidence where applicable.

## 8. Reproducibility

The generator must accept configurable dataset sizes and a fixed seed.
Two runs using identical settings must produce identical data outputs.
Record row counts, file checksums, validation results and the seed.
