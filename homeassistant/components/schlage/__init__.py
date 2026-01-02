"""The Schlage integration."""

from __future__ import annotations

from pycognito.exceptions import WarrantException
import pyschlage

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import CONF_MAX_RETRIES, CONF_RETRY_DELAY, MAX_RETRIES, RETRY_DELAY
from .coordinator import SchlageConfigEntry, SchlageDataUpdateCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.LOCK,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: SchlageConfigEntry) -> bool:
    """Set up Schlage from a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    try:
        auth = await hass.async_add_executor_job(pyschlage.Auth, username, password)
    except WarrantException as ex:
        raise ConfigEntryAuthFailed from ex

    retry_delay = entry.options.get(CONF_RETRY_DELAY, RETRY_DELAY)
    max_retries = entry.options.get(CONF_MAX_RETRIES, MAX_RETRIES)

    coordinator = SchlageDataUpdateCoordinator(
        hass, entry, username, pyschlage.Schlage(auth), retry_delay, max_retries
    )
    entry.runtime_data = coordinator
    await coordinator.async_config_entry_first_refresh()
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SchlageConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

async def async_reload_entry(hass: HomeAssistant, entry: SchlageConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)