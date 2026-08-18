"""Configuration loading with secret-safe errors.

Two rules shape this module:

1. A missing or malformed setting must produce an error a developer can act on
   without printing the value, because these values are connection strings and
   tokens (Increment 0, "configuration loading with secret-safe errors").
2. The development authentication mode must be impossible to enable by
   accident. It is refused unless the service is explicitly told it is running
   locally, so a deployed environment cannot fall back to it.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Literal

AuthMode = Literal["dev", "oidc"]


class ConfigurationError(RuntimeError):
    """A setting is missing or unusable. Never carries the value."""


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigurationError(
            f"{name} is not set. Copy .env.example to .env.local and fill it in."
        )
    return value


def _optional(name: str, default: str) -> str:
    return os.environ.get(name, "").strip() or default


def redact_dsn(dsn: str) -> str:
    """Render a connection string safe for logs and error messages."""
    return re.sub(r"://([^:/@]+)(:[^@]*)?@", r"://\1:***@", dsn)


@dataclass(frozen=True)
class Settings:
    database_url: str
    auth_mode: AuthMode
    log_level: str
    environment: str

    @property
    def safe_database_url(self) -> str:
        return redact_dsn(self.database_url)


def load_settings() -> Settings:
    database_url = _require("DATABASE_URL_API")

    environment = _optional("APP_ENVIRONMENT", "local")
    auth_mode = _optional("AUTH_MODE", "oidc")

    if auth_mode not in ("dev", "oidc"):
        raise ConfigurationError(
            f"AUTH_MODE must be 'dev' or 'oidc', received an unsupported value "
            f"of length {len(auth_mode)}."
        )

    if auth_mode == "dev" and environment != "local":
        # The dev verifier trusts a header. That is acceptable on a developer's
        # machine and nowhere else, so refuse to start rather than warn.
        raise ConfigurationError(
            "AUTH_MODE=dev is only permitted when APP_ENVIRONMENT=local. "
            f"This process has APP_ENVIRONMENT={environment}."
        )

    return Settings(
        database_url=database_url,
        auth_mode=auth_mode,  # type: ignore[arg-type]
        log_level=_optional("LOG_LEVEL", "INFO").upper(),
        environment=environment,
    )
