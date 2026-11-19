"""Constants of the integration."""
from __future__ import annotations

DOMAIN = "weishaupt"

CONF_REQUEST_GAP = "request_gap"
CONF_CYCLIC_INTERVAL = "cyclic_interval"
CONF_WRITES_ENABLED = "writes_enabled"
CONF_TELEGRAM_DB = "telegram_db"
CONF_MAX_WRITES_PER_HOUR = "max_writes_per_hour"
DEFAULT_TELEGRAM_DB = "/share/ebusd/telegrams.db"  # the telegram log of the ebusd add-on of the test installation

# Load on the bus. No interval is established by a record: these are choices, explained in the README.
DEFAULT_REQUEST_GAP = 2  # seconds between two requests that may go to the bus, whatever is due
MIN_REQUEST_GAP, MAX_REQUEST_GAP = 1, 30
DEFAULT_CYCLIC_INTERVAL = 300  # live values
MIN_CYCLIC_INTERVAL, MAX_CYCLIC_INTERVAL = 60, 3600
PASSIVE_INTERVAL = 30  # passive messages: read from ebusd's cache, never requested from the bus
PASSIVE_MAX_AGE = 900  # a passive value older than this is not shown
SETTING_INTERVAL = 6 * 3600  # settings and diagnostics: read at start, then rarely
COUNTER_INTERVAL = 3600  # counters and the fault memory
PROGRAM_INTERVAL = 24 * 3600  # weekly programs
RETRY_INTERVAL = 60  # after a failed or invalid reading
NO_SIGNAL_PAUSE = 60  # no request while ebusd reports no signal
CONNECTION_RETRY = 30
FAILURES_BEFORE_UNKNOWN = 3  # consecutive failed readings before the value of a message is dropped

MANUFACTURER = "Weishaupt"
MODELS = {"boiler": "WTC", "manager": "WCM-KA", "module": "WCM-EM", "room": "WCM-FS"}
DOCUMENTATION_URL = "https://github.com/aghulas/ha-weishaupt"

# Writes
EVENT_WRITE = f"{DOMAIN}_write"
EVENT_CHANGE = f"{DOMAIN}_change"  # one per change asked by a user, for the logbook (logbook.py)
PENDING_TTL = 900  # seconds a requested change of a regulation setting waits for its confirmation
JOURNAL_SIZE = 50  # writes kept for the diagnostics download
