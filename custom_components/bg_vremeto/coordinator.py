"""Coordinator for BG Vremeto weather data."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import async_timeout
from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_LOCATION,
    CONF_PROVIDER,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PROVIDER_DALIVALI,
)
from .providers import async_fetch_weather

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 10


class BGVremetoDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Class to manage fetching BG Vremeto data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.provider = entry.data.get(CONF_PROVIDER, PROVIDER_DALIVALI)
        self.location = str(entry.data[CONF_LOCATION])
        self.session = async_get_clientsession(hass)
        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        if isinstance(scan_interval, (int, float)):
            update_interval = timedelta(seconds=scan_interval)
        else:
            update_interval = scan_interval
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.provider}_{self.location}",
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict:
        try:
            async with async_timeout.timeout(REQUEST_TIMEOUT):
                data = await async_fetch_weather(
                    provider=self.provider,
                    location=self.location,
                    session=self.session,
                )
        except (asyncio.TimeoutError, ClientError) as err:
            raise UpdateFailed(f"Error fetching BG Vremeto data: {err}") from err
        except Exception as err:  # pragma: no cover - defensive parsing guard
            raise UpdateFailed(f"Error parsing BG Vremeto data: {err}") from err
        if not data:
            raise UpdateFailed("No weather data found in provider response")

        return data
