# Data Platform — Startup and Integration Guide

## Overview

This guide documents how to start the local data platform, verify service readiness, and execute integration tests.

### Infrastructure

| Component | Deployment | Purpose |
|---|---|---|
| PostgreSQL | Local WSL service | Analytics and Polaris metadata |
| MinIO | Local WSL service | S3-compatible object storage |
| Apache Polaris | Docker Compose | Apache Iceberg REST catalog |
| DuckDB | Python / uv | SQL processing and Iceberg queries |
| PyIceberg | Python / uv | Iceberg catalog and table operations |
| dbt-duckdb | Python / uv | Data transformation and modeling |

## 1. Prerequisites

Ensure WSL, Docker, Python 3.12, uv, PostgreSQL, and MinIO are installed and configured.

Required configuration files:

- `infra/.env` — Polaris and MinIO credentials used by the infrastructure and Python utilities.
- `.env.fish` — Local Fish development credentials.
- `infra/compose.yaml` — Polaris container configuration.
- `infra/polaris/keys/` — Polaris authentication key pair.

Never commit passwords, access keys, or private keys to Git.

## 2. Start PostgreSQL

```bash
sudo systemctl start postgresql
sudo systemctl status postgresql
```

Verify connectivity:

```bash
pg_isready -h localhost -p 5432
```

The platform uses two separate databases:

- `analytics` — Gold serving and analytics.
- `polaris` — Polaris catalog metadata, using `polaris_schema`.

## 3. Start MinIO

```bash
sudo systemctl start minio
sudo systemctl status minio
```

Verify API readiness:

```bash
curl -f http://127.0.0.1:9000/minio/health/live
```

MinIO must be accessible before running Iceberg data read/write operations.

## 4. Start Apache Polaris

From the project root:

```bash
docker compose --env-file infra/.env -f infra/compose.yaml up -d polaris
```

Check container status:

```bash
docker compose --env-file infra/.env -f infra/compose.yaml ps
```

Check logs:

```bash
docker logs data-platform-polaris --tail 50
```

Verify Polaris health:

```bash
curl -f http://127.0.0.1:8182/q/health
```

The health endpoint must report readiness before executing catalog operations.

**Important:** The configured PostgreSQL address `172.18.0.1` is specific to the current Docker networking environment. If the Docker network changes, Polaris may lose access to its metadata database.

### Polaris bootstrap

The `polaris-bootstrap` service belongs to the Compose `setup` profile and is intended for initial catalog realm setup.

Do not run bootstrap as part of routine startup.

## 5. Activate the development environment

From a Fish shell:

```fish
source scripts/dev-env.fish
```

This activates the Python virtual environment, loads local credentials, exports PostgreSQL settings, and changes into the dbt project directory.

Return to the repository root before running the commands below.

## 6. Validate the platform

### Automated tests

```bash
uv run pytest -v
```

Current baseline: 9 passing tests.

### Polaris connectivity

```bash
uv run python scripts/test_polaris_connection.py
```

Expected namespaces: `bronze`, `silver`, `gold`.

### Iceberg table persistence

```bash
uv run python scripts/test_iceberg_table.py
```

Validates the existing test table, conditionally inserts fixture records, and verifies persisted data.

### DuckDB–Iceberg integration

```bash
uv run python scripts/test_duckdb_iceberg.py
```

Expected fixture:

```text
[(1, 'bronze'), (2, 'silver'), (3, 'gold')]
```

The integration test should report `PASSED`.

## 7. Troubleshooting

| Problem | Initial checks |
|---|---|
| PostgreSQL connection refused | PostgreSQL service, port 5432, network binding |
| Polaris container fails to start | Docker logs, database connectivity, credentials |
| Polaris authentication fails | Client credentials, realm header, OAuth endpoint |
| MinIO access denied | S3 credentials, bucket policy, endpoint |
| Iceberg table not found | Catalog, namespace, table identifier |
| DuckDB extension error | Installed extensions and DuckDB version |
| pytest import mismatch | Duplicate test module names and pytest discovery configuration |

## 8. Startup dependency summary

1. Start PostgreSQL.
2. Start MinIO.
3. Start Docker and Apache Polaris.
4. Verify service health.
5. Activate the Python development environment.
6. Run automated tests.
7. Run live integration checks.

PostgreSQL and MinIO can start independently. Polaris requires access to its PostgreSQL metadata database. Iceberg read/write operations additionally require access to MinIO.

## 9. Shutdown

Stop Polaris:

```bash
docker compose --env-file infra/.env -f infra/compose.yaml stop polaris
```

PostgreSQL and MinIO may remain running for other local development tasks. Stop them only when appropriate.

Do not use `docker compose down -v` as a routine shutdown command.

---

**Status:** Integration hardening baseline validated. Ready for Bronze-to-Silver transformation testing.