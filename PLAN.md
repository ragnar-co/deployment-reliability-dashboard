# Deployment Reliability Dashboard Delivery Plan

## Goal

Build a small internal web application that lets DevOps identify which service
needs investigation first after deployment failures. The application imports a
deployment-history CSV, stores validated data in SQLite, and shows service-level
reliability metrics plus the failed deployments behind them.

The delivery ends when the working code, tests or validation evidence,
documentation, and source are pushed to the GitHub repository and the app is
deployed through Coolify and reachable. The optional AI workflow is not part of
this delivery. (Updated 2026-10-02: Coolify was added to scope to match the
original assignment.)

## Scope

### Included

- Upload one deployment-history CSV at a time.
- Validate the required columns and row-level values before saving.
- Store imported rows in SQLite atomically.
- Show total deployments, successful deployments, failed deployments, and
  overall success rate.
- Show deployment count, success rate, and average successful duration for each
  service.
- Filter the dashboard by service. An environment filter is a small,
  non-blocking enhancement if time permits.
- List failed deployments with service, environment, date, duration, and error
  message.
- Provide automated tests or repeatable validation for import, aggregation,
  filtering, and failure listing.

### Excluded

- Production operations, authentication, and role-based access control.
- AI-generated investigation proposals.
- Live CI/CD or log-provider integrations.
- Multi-instance database scaling and concurrent bulk imports.

## Chosen Approach

- Documentation blueprint: `ddd-web-app`.
- Application shape: a small server-rendered web application with a JSON API
  only where it simplifies the UI.
- Persistence: SQLite3. The supplied data volume is modest and this choice
  minimizes setup time for a single-instance MVP.
- Import semantics: validate the whole file first, then write it in one
  transaction. `deployment_id` is unique. Exact repeat uploads are detected by
  a file checksum and must not create a second copy of the same data.

## Delivery Sequence

| Timebox | Work | Evidence of completion |
| --- | --- | --- |
| 0-15 min | Create the project skeleton and the DDD web-app documentation outline. Confirm the CSV contract and MVP acceptance criteria. | Project starts locally; requirements and assumptions are documented. |
| 15-35 min | Create SQLite schema and CSV import validation. Add an import-batch record, checksum, and transactional insert. | Valid sample CSV imports; malformed input is rejected without partial data. |
| 35-60 min | Implement metric queries and service filtering. | Metrics agree with known CSV totals and filtering changes the result set. |
| 60-80 min | Implement the dashboard and failed-deployment list. | A user can upload, select a service, and inspect the associated failures. |
| 80-95 min | Add tests and a local validation command. | Tests or repeatable checks pass. |
| 95-110 min | Complete README and run a clean local smoke test from the documented steps. | Another developer can run and verify the app locally. |
| 110-120 min | Commit and push to the GitHub repository, then deploy through Coolify (`docs/DEPLOYMENT.md`). | Commit SHA recorded; `/health` returns 200 on the Coolify URL. |

## Data Model

### `import_batches`

Tracks each accepted source file: `id`, `original_filename`, `sha256`,
`imported_at`, `row_count`, `success_count`, `failed_count`, and `status`.

### `deployments`

Stores the dashboard facts: `deployment_id`, `service_name`, `status`,
`duration_seconds`, `error_message`, `deployment_date`, `environment`, and
`batch_id`.

Required indexes are `deployment_id` (unique), `service_name`, `status`, and
`deployment_date`.

## Metric Definitions

- **Deployment count:** all imported deployment records in the selected filter.
- **Success rate:** `successful deployments / all deployments * 100`.
- **Average successful duration:** arithmetic mean of `duration_seconds` where
  `status = success`; failures are not included.
- **Failed deployment list:** records where `status = failed`, ordered newest
  first and filterable by service.

## Minimum DDD Web-App Documents

Write the selected documents in their dependency order. The first working set
is `PERSONAS`, `CONSTRAINTS`, `VPD`, `SCOPE`, `PRD`, `GLOSSARY`,
`ARCHITECTURE`, `DATA_MODEL`, `UI_SPEC`, `SECURITY`, `API_SPEC`, `TASKS`,
`TESTING`, and `README`, plus `DEPLOYMENT` (Coolify steps and launch blockers)
and `ADR`.

## Acceptance Criteria

- The supplied CSV is accepted and produces the expected dashboard totals.
- A CSV missing a required column, containing an invalid status, invalid date,
  non-positive duration, or duplicate `deployment_id` is rejected with a clear
  error and no partial import.
- The all-service view and every selected-service view show correct metrics.
- Failed rows display their original error messages.
- A documented local test or validation command passes before pushing.
- The repository contains no credentials, SQLite database file, or uploaded CSV
  data by default.

## Handoff Dependencies

The repository URL and push permission, a Coolify instance with a Git source,
and confirmation that access is restricted to the internal network are required
for the final handoff (`docs/DEPLOYMENT.md`, Launch Blockers). Credentials are
never stored in the repository.
