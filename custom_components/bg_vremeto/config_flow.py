"""Config flow for BG Vremeto weather integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_LOCATION,
    CONF_NAME,
    CONF_PROVIDER,
    CONF_SCAN_INTERVAL,
    DEFAULT_PROVIDER,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PROVIDERS,
    PROVIDER_DALIVALI,
)


class BGVremetoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BG Vremeto."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            provider = user_input[CONF_PROVIDER]
            location = _normalize_location(provider, user_input[CONF_LOCATION])
            if location is None:
                errors[CONF_LOCATION] = "invalid_location"
            else:
                unique_id = f"{provider}:{location}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                name = user_input.get(CONF_NAME) or f"{PROVIDERS[provider]} {location}"
                data = {
                    CONF_PROVIDER: provider,
                    CONF_LOCATION: location,
                    CONF_NAME: name,
                    CONF_SCAN_INTERVAL: user_input.get(
                        CONF_SCAN_INTERVAL, int(DEFAULT_SCAN_INTERVAL.total_seconds())
                    ),
                }

                return self.async_create_entry(title=name, data=data)

        schema = vol.Schema(
            {
                vol.Required(CONF_PROVIDER, default=DEFAULT_PROVIDER): vol.In(PROVIDERS),
                vol.Required(CONF_LOCATION): cv.string,
                vol.Optional(CONF_NAME): cv.string,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=int(DEFAULT_SCAN_INTERVAL.total_seconds())
                ): cv.positive_int,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


@callback
def async_get_options_flow(config_entry: config_entries.ConfigEntry):
    return BGVremetoOptionsFlowHandler(config_entry)


class BGVremetoOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for BG Vremeto."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=options.get(
                        CONF_SCAN_INTERVAL,
                        self.config_entry.data.get(
                            CONF_SCAN_INTERVAL, int(DEFAULT_SCAN_INTERVAL.total_seconds())
                        ),
                    ),
                ): cv.positive_int,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)


def _normalize_location(provider: str, value: str) -> str | None:
    location = value.strip()
    if not location:
        return None
    if provider == PROVIDER_DALIVALI:
        return location if location.isdigit() else None
    return location
