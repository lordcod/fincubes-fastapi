import json
import logging

import sentry_sdk
from cordlog import setup_logging as setup_cordlog
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.core.config import settings

config_path = "app/core/config/log_config.json"

if settings.SENTRY_DNS:
    sentry_logging = LoggingIntegration(
        level=logging.DEBUG,
        event_level=logging.WARNING
    )
    sentry_sdk.init(
        dsn=settings.SENTRY_DNS,
        send_default_pii=True,
        integrations=[FastApiIntegration(), sentry_logging],
        traces_sample_rate=0.1,
        environment="production",
        release="fincubes-fastapi@0.0.0",
    )


def setup_logging():
    with open(config_path, "rb") as f:
        config = json.loads(f.read())
    setup_cordlog(config)
