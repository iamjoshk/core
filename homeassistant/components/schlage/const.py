"""Constants for the Schlage integration."""

from datetime import timedelta
import logging

DOMAIN = "schlage"
LOGGER = logging.getLogger(__package__)
MANUFACTURER = "Schlage"
UPDATE_INTERVAL = timedelta(seconds=30)
CONF_RETRY_DELAY = "retry_delay"
CONF_MAX_RETRIES = "max_retries"
RETRY_DELAY = 5  # seconds
MAX_RETRIES = 1