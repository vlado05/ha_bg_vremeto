"""Provider fetch helpers for BG Vremeto."""
from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import ClientSession

from .const import PROVIDER_DALIVALI, PROVIDER_SINOPTIK
from .parser import parse_dalivali_html
from .sinoptik_parser import parse_sinoptik_html

DALIVALI_URL = "https://www.dalivali.bg/?location={location}"
SINOPTIK_URL = "https://www.sinoptik.bg/{location}"

USER_AGENT = "Home Assistant (BG Vremeto)"


async def async_fetch_weather(
    *, provider: str, location: str, session: ClientSession
) -> dict[str, Any]:
    """Fetch and parse weather data for a provider."""
    if provider == PROVIDER_DALIVALI:
        url = DALIVALI_URL.format(location=location)
        html = await _fetch(session, url)
        return parse_dalivali_html(html)

    if provider == PROVIDER_SINOPTIK:
        base = SINOPTIK_URL.format(location=location)
        current_url = base
        hourly_url = f"{base}/hourly"
        daily_url = f"{base}/5-days"
        current_html, hourly_html, daily_html = await asyncio.gather(
            _fetch(session, current_url),
            _fetch(session, hourly_url),
            _fetch(session, daily_url),
        )
        return parse_sinoptik_html(current_html, hourly_html, daily_html)

    raise ValueError(f"Unsupported provider: {provider}")


async def _fetch(session: ClientSession, url: str) -> str:
    response = await session.get(url, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return await response.text()
