SUPPORTED_SCHEMA = "1.0"
SUPPORTED_ENGINE_VERSION = "1.0"


def validate_registry(
    schema_version: str,
    engine_version: str,
) -> None:
    if schema_version != SUPPORTED_SCHEMA:
        raise ValueError("unsupported schema version")

    if engine_version != SUPPORTED_ENGINE_VERSION:
        raise ValueError("unsupported engine version")
