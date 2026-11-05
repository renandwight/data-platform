"""Validate connectivity to the Polaris Iceberg REST catalog."""

from data_platform.config.settings import load_settings
from data_platform.connections.polaris import create_iceberg_catalog


def main() -> None:
    settings = load_settings()
    catalog = create_iceberg_catalog(settings)

    namespaces = sorted(namespace[0] for namespace in catalog.list_namespaces())

    print("Polaris authentication: successful")
    print(f"PyIceberg catalog: {settings.polaris_catalog}")
    print("Namespaces:", ", ".join(namespaces))

    expected = {"bronze", "silver", "gold"}

    if set(namespaces) != expected:
        raise RuntimeError(f"Unexpected namespaces: {namespaces}")

    print("Namespace verification: PASSED")


if __name__ == "__main__":
    main()
