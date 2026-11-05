"""Tests for centralized configuration management."""

import pytest

from data_platform.config.settings import load_env_file, load_settings


def test_load_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# Test credentials\n"
        "POLARIS_CLIENT_SECRET='test-secret'\n"
        "POLARIS_S3_ACCESS_KEY=test-access\n"
        "POLARIS_S3_SECRET_KEY=test-key\n"
    )

    values = load_env_file(env_file)

    assert values["POLARIS_CLIENT_SECRET"] == "test-secret"
    assert values["POLARIS_S3_ACCESS_KEY"] == "test-access"


def test_missing_env_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_env_file(tmp_path / "missing.env")


def test_missing_credentials(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("POLARIS_CLIENT_SECRET=test-secret\n")

    for name in (
        "POLARIS_CLIENT_SECRET",
        "POLARIS_S3_ACCESS_KEY",
        "POLARIS_S3_SECRET_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ValueError, match="Missing required configuration"):
        load_settings(env_file)


def test_environment_override(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "POLARIS_CLIENT_SECRET=file-secret\n"
        "POLARIS_S3_ACCESS_KEY=test-access\n"
        "POLARIS_S3_SECRET_KEY=test-key\n"
    )

    monkeypatch.setenv("POLARIS_CLIENT_SECRET", "environment-secret")

    settings = load_settings(env_file)

    assert settings.polaris_client_secret == "environment-secret"
    assert settings.polaris_catalog == "lakehouse"
