import json

from cordlog import setup_logging as setup_cordlog

config_path = "app/core/config/log_config.json"


def setup_logging():
    with open(config_path, "rb") as f:
        config = json.loads(f.read())
    setup_cordlog(config)
