"""Constants of the Weishaupt integration."""
from datetime import timedelta

DOMAIN = "weishaupt"

CONF_TELEGRAM_DB = "telegram_db"
CONF_WRITES_ENABLED = "writes_enabled"

DEFAULT_PORT = 8888
DEFAULT_TELEGRAM_DB = "/share/ebusd/telegrams.db"
SCAN_INTERVAL = timedelta(minutes=5)
