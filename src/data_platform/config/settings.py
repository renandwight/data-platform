"""Centralized configuration for data platform integrations."""

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENV_FILE = PROJECT_ROOT / "infra" / ".env"


def load_env_file(path: Path) -> dict[str, str]:
    """Load simple KEY=VALUE entries from a local environment file."""
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    values = {}

    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        key, separator, value = line.partition("=")

        if not separator:
            raise ValueError(f"Invalid configuration entry at line {line_number}")

        values[key.strip()] = value.strip().strip("\"'")

    return values


@dataclass(frozen=True)
class Settings:
    polaris_url: str
    polaris_realm: str
    polaris_catalog: str
    polaris_warehouse: str
    polaris_client_id: str
    polaris_client_secret: str
    minio_endpoint: str
    minio_region: str
    minio_access_key: str
    minio_secret_key: str


def load_settings(env_file: Path = DEFAULT_ENV_FILE) -> Settings:
    """Load configuration with environment variables taking precedence."""
    file_values = load_env_file(env_file)

    def get_value(name: str, default: str = "") -> str:
        return os.environ.get(name, file_values.get(name, default))

    required = (
        "POLARIS_CLIENT_SECRET",
        "POLARIS_S3_ACCESS_KEY",
        "POLARIS_S3_SECRET_KEY",
    )

    missing = [name for name in required if not get_value(name)]

    if missing:
        raise ValueError("Missing required configuration: " + ", ".join(missing))

    return Settings(
        polaris_url=get_value("POLARIS_URL", "http://127.0.0.1:8181"),
        polaris_realm=get_value("POLARIS_REALM", "POLARIS"),
        polaris_catalog=get_value("POLARIS_CATALOG", "lakehouse"),
        polaris_warehouse=get_value("POLARIS_WAREHOUSE", "lakehouse"),
        polaris_client_id=get_value("POLARIS_CLIENT_ID", "root"),
        polaris_client_secret=get_value("POLARIS_CLIENT_SECRET"),
        minio_endpoint=get_value("MINIO_ENDPOINT", "http://127.0.0.1:9000"),
        minio_region=get_value("MINIO_REGION", "us-east-1"),
        minio_access_key=get_value("POLARIS_S3_ACCESS_KEY"),
        minio_secret_key=get_value("POLARIS_S3_SECRET_KEY"),
    )
