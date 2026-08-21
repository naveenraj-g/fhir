from typing import Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class RoutesConfig(BaseModel):
    # Which routers get mounted under /api/v1 at startup — see
    # app.routers.discover_routers(). Not listed = not mounted.
    enabled: list[str] = Field(default_factory=list)


class LogConfig(BaseModel):
    """Observability config — consumed by app.core.logging.setup_logging(),
    app.middleware.access_log, and app.core.database's query listeners."""

    # Root log level. DEBUG turns on the per-layer flow logging that the
    # service and repository emit; INFO keeps only business outcomes and the
    # access log.
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # "json" (one JSON object per line — what log aggregators want) or
    # "console" (flat, human-readable; local development only).
    format: Literal["json", "console"] = "json"

    # Both of the above are matched case-insensitively: `format: JSON` and
    # `level: debug` are as valid as the canonical spellings. Without this a
    # perfectly reasonable edit to configs/config.yaml crashes the app at
    # import time with a pydantic literal_error — a hostile failure mode for
    # the two settings people actually hand-edit.
    @field_validator("level", "format", mode="before")
    @classmethod
    def _normalise_case(cls, v):
        if isinstance(v, str):
            return v.upper() if v.upper() in _LOG_LEVELS else v.lower()
        return v

    # ⚠️ PHI. Logs full request payloads at DEBUG via log_payload(). The
    # documents staged here are medical records — enabling this writes
    # attachment titles, patient ids and every extracted Observation value
    # into the log stream. Local development only; `redact` below is a
    # backstop for obvious secrets, NOT a PHI safeguard.
    debug_payloads: bool = False

    # Any SQL statement slower than this logs a `db.slow_query` WARNING.
    slow_query_ms: int = 500

    # Log every SQL statement at DEBUG (very noisy — debugging only).
    sql_echo: bool = False

    # Re-enable Uvicorn's own per-request access line. Off by default because
    # it duplicates app.middleware.access_log's richer `http.request` line and
    # — since the `uvicorn.access` logger sets propagate=False and keeps its
    # own handler — bypasses our formatter, emitting PLAIN TEXT even when
    # format is "json".
    uvicorn_access: bool = False

    # Field names masked by log_payload() even when debug_payloads is on.
    # Matched case-insensitively against dict keys at any nesting depth.
    redact: list[str] = Field(
        default_factory=lambda: ["authorization", "token", "password", "secret"]
    )


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    STAGING_DATABASE_URL: str

    routes: RoutesConfig = Field(default_factory=RoutesConfig)
    logging: LogConfig = Field(default_factory=LogConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Precedence, highest first: real env var > `.env` >
        `configs/config.yaml` > field defaults. `.env` stays reserved for the
        one true per-environment secret (the database URL); everything else —
        logging, which routes are enabled — is checked-in application behavior
        that lives in `configs/config.yaml` instead.

        A future secrets-manager source (e.g. AWS Secrets Manager/SSM) would
        slot into this same tuple as another `PydanticBaseSettingsSource`,
        ranked between `env_settings` and `dotenv_settings` — no changes
        needed anywhere else, since consumers only ever read `settings.*`.
        """
        # yaml_file_encoding is explicit because the source otherwise opens the
        # file with the platform default — cp1252 on Windows, which blows up on
        # any non-ASCII byte in the committed config (e.g. the ⚠️ in the
        # debug_payloads PHI warning).
        yaml_settings = YamlConfigSettingsSource(
            settings_cls,
            yaml_file="configs/config.yaml",
            yaml_file_encoding="utf-8",
        )
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            yaml_settings,
            file_secret_settings,
        )


settings = Settings()
