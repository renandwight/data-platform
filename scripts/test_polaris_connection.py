
from pathlib import Path

import requests
from pyiceberg.catalog import load_catalog

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / "infra" / ".env"

POLARIS_URL = "http://127.0.0.1:8181"
REALM = "POLARIS"


def load_local_secrets(path: Path) -> dict[str, str]:
    secrets = {}

    for line in path.read_text().splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        key, separator, value = line.partition("=")

        if separator:
            secrets[key.strip()] = value.strip().strip("\"'")

    return secrets


def main() -> None:
    secrets = load_local_secrets(ENV_FILE)
    client_secret = secrets["POLARIS_CLIENT_SECRET"]

    response = requests.post(
        f"{POLARIS_URL}/api/catalog/v1/oauth/tokens",
        headers={"Polaris-Realm": REALM},
        auth=("root", client_secret),
        data={
            "grant_type": "client_credentials",
            "scope": "PRINCIPAL_ROLE:ALL",
        },
        timeout=15,
    )

    response.raise_for_status()
    token = response.json()["access_token"]

    catalog = load_catalog(
        "lakehouse",
        type="rest",
        uri=f"{POLARIS_URL}/api/catalog",
        warehouse="lakehouse",
        token=token,
        **{
        "header.Polaris-Realm": REALM,
        "py-io-impl": "pyiceberg.io.pyarrow.PyArrowFileIO",
        "s3.endpoint": "http://127.0.0.1:9000",
        "s3.region": "us-east-1",
        "s3.access-key-id": secrets["POLARIS_S3_ACCESS_KEY"],
        "s3.secret-access-key": secrets["POLARIS_S3_SECRET_KEY"],
        "s3.force-virtual-addressing": False,
        },
    )

    namespaces = sorted(
        namespace[0] for namespace in catalog.list_namespaces()
    )

    print("Polaris authentication: successful")
    print("PyIceberg catalog: lakehouse")
    print("Namespaces:", ", ".join(namespaces))

    expected = {"bronze", "silver", "gold"}

    if set(namespaces) != expected:
        raise RuntimeError(
            f"Unexpected namespaces: {namespaces}"
        )

    print("Namespace verification: PASSED")


if __name__ == "__main__":
    main()
