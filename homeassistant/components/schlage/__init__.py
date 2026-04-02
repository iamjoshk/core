"""The Schlage integration."""

from __future__ import annotations

from pycognito.exceptions import WarrantException
import pyschlage
import voluptuous as vol

from homeassistant.components.lock import DOMAIN as LOCK_DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant, SupportsResponse
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import config_validation as cv, service
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_MAX_RETRIES,
    CONF_RETRY_DELAY,
    DOMAIN,
    MAX_RETRIES,
    RETRY_DELAY,
    SERVICE_ADD_CODE,
    SERVICE_DELETE_CODE,
    SERVICE_GET_CODES
)
from .coordinator import SchlageConfigEntry, SchlageDataUpdateCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.LOCK,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Schlage component."""
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        SERVICE_ADD_CODE,
        entity_domain=LOCK_DOMAIN,
        schema={
            vol.Required("name"): cv.string,
            vol.Required("code"): cv.matches_regex(r"^\d{4,8}$"),
        },
        func=SERVICE_ADD_CODE,
    )

    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        SERVICE_DELETE_CODE,
        entity_domain=LOCK_DOMAIN,
        schema={
            vol.Required("name"): cv.string,
        },
        func=SERVICE_DELETE_CODE,
    )

    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        SERVICE_GET_CODES,
        entity_domain=LOCK_DOMAIN,
        schema=None,
        func=SERVICE_GET_CODES,
        supports_response=SupportsResponse.ONLY,
    )

    return True


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