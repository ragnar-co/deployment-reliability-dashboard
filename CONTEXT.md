# Deployment Reliability Dashboard Context

## Purpose

This file is the working context for building the Deployment Reliability
Dashboard. It records the agreed product scope, known facts from the supplied
CSV, and decisions that should not be silently changed during implementation.

## Product Problem

The development team deploys many services regularly. When deployments fail,
DevOps must inspect histories in several places to decide where to start. This
application consolidates exported deployment history and prioritizes services
through visible reliability metrics and the underlying failure details.

## Users

- **DevOps operator:** imports a deployment export, filters services, and reads
  failure messages to begin investigation.
- **Engineering lead:** compares service reliability and identifies the service
  that needs attention first.

## Current Assignment Boundary

The required MVP must:

1. Accept a sample deployment-history CSV.
2. Validate and store it in SQLite3 or DuckDB.
3. Display deployment count, success rate, and average duration of successful
   deployments by service.
4. Display failed deployments and their error messages.
5. Let the user select a service to narrow the dashboard.
6. Include tests or repeatable validation.
7. Be pushed to the company GitHub repository within 120 minutes.
8. Be deployed through Coolify and reachable (updated scope, 2026-10-02: the
   original assignment requires it; an earlier draft of this file deferred it).

The optional AI workflow remains deferred and must not delay the MVP. The
architecture keeps one extension point for it (`docs/ARCHITECTURE.md`,
Third-party Integrations).

## Input Data Contract

Source file: `theBeth_deployments_mock.csv`

Required columns:

| Column | Meaning | Validation |
| --- | --- | --- |
| `deployment_id` | Deployment identifier | Required and unique. |
| `service_name` | Service being deployed | Required non-empty text. |
| `status` | Outcome | Exactly `success` or `failed`. |
| `duration_seconds` | Deployment duration | Required positive integer. |
| `error_message` | Failure detail | Empty for success; required for failed records. |
| `deployment_date` | Deployment date | Required ISO date `YYYY-MM-DD`. |
| `environment` | Target environment | Required non-empty text. |

## Observed CSV Profile

The supplied mock CSV is approximately 2.1 MB and contains 36,527 deployment
records across 24 services, from 2026-07-03 through 2026-09-30.

| Measure | Observed value |
| --- | ---: |
| Successful deployments | 33,643 |
| Failed deployments | 2,884 |
| Overall success rate | 92.10% |
| Average successful duration | 187.8 seconds |
| Staging deployments | 25,488 |
| Production deployments | 11,039 |

The observed sample has unique deployment IDs, valid statuses, positive
durations, parseable dates, no error message on successful records, and an
error message on every failed record. These observations are sample facts, not
guarantees about later uploads.

## Priority Signals in the Sample

The lowest observed service success rates are:

| Service | Failures | Success rate |
| --- | ---: | ---: |
| `release-validator` | 316 | 79.29% |
| `log-ingestion` | 240 | 84.70% |
| `report-worker` | 225 | 85.71% |
| `workflow-engine` | 189 | 87.34% |
| `integration-gateway` | 173 | 88.23% |

The most frequent failure messages in the sample are upstream dependency
timeouts, missing `APP_CONFIG`, health-check timeouts, migration-lock timeouts,
image-pull registry timeouts, and database connection refusals.

Staging has a 90.65% success rate, below production at 95.46%. An environment
filter is therefore useful if it fits the delivery timebox, but the mandatory
filter is service.

## Product Decisions

- Use `ddd-web-app`, because the deliverable is an application with upload,
  persistence, UI, and API behavior.
- Stack: Python 3.12, FastAPI, Jinja2, SQLite3 (decisions recorded in `docs/ADR.md`).
- Documentation set: all 20 `ddd-web-app` documents in `docs/`, in the
  blueprint's `generation_order`. `docs/` is the source of truth where it is
  more detailed than this file.
- Upload limit is 10 MiB with a UI warning before upload.
- Average successful duration is shown with two decimals (half-up).
- Use SQLite3 for the MVP. The data volume and expected single-instance use are
  well within its scope.
- Import must be atomic: a failed validation leaves no partial deployment data.
- Store import metadata and a SHA-256 checksum to make repeated uploads
  detectable.
- Treat `deployment_id` as a global unique key. Do not silently overwrite an
  existing deployment.
- Default the service filter to all services.
- Show duration in seconds unless the UI deliberately adds a human-friendly
  equivalent without changing the authoritative stored value.
- Do not include real credentials, company URLs, or imported data in commits.

## Explicit Non-Goals

- Root-cause determination from deployment data alone.
- Automated remediation or deployment rollback.
- Authentication and authorization.
- Multiple application instances, high-concurrency import handling, or a
  managed database.
- AI investigation drafts, model calls, prompts, or provider quotas.

## Deferred AI Workflow Notes

If the bonus is later authorized, it should create a draft investigation
proposal only from selected failed deployments. Every recommendation must cite
the relevant `deployment_id` and error message. Store the generated draft with
its selected deployment IDs, creation time, prompt version, model identifier,
and review status. It is an investigation aid, not a verified root cause.

## Known Dependencies and Risks

- The application has no authentication (non-goal). Coolify access must be
  restricted to the internal network before the app is exposed.
- Deployment persistence on Coolify requires a persistent volume mounted at
  `/data` for SQLite. Launch blockers are listed in `docs/DEPLOYMENT.md`.
- A future production data source should add an exact timestamp, deployment
  version or commit SHA, service ownership, and links to detailed logs. The
  current CSV does not provide these fields.

## Implementation Guardrails

- Never evaluate dashboard metrics from raw CSV after import; read from SQLite
  so upload behavior and displayed data agree.
- Parameterize all filter queries.
- Keep uploaded files and `*.db` files out of Git.
- Add tests for both valid and invalid imports, duplicate detection, aggregate
  formulas, filtering, and failure-list contents.
- Record any change to the data contract or metric formula in the project
  documentation before changing implementation behavior.
