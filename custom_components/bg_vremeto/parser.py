"""HTML parsing helpers for DaliVali weather data."""
from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup


def parse_dalivali_html(html: str) -> dict[str, Any]:
    """Parse DaliVali HTML into structured weather data."""
    soup = BeautifulSoup(html, "html.parser")
    city_wrap = soup.select_one("div.city-weather-wrap")
    if not city_wrap:
        return {}

    data: dict[str, Any] = {
        "city": _get_text(city_wrap.select_one(".main-title-wrap .name")),
        "current": _parse_current(city_wrap),
        "hourly": _parse_hourly(city_wrap),
        "daily": _parse_daily(city_wrap),
    }

    return data


def _parse_current(city_wrap: Any) -> dict[str, Any]:
    current_section = city_wrap.select_one(".current-weather")
    if not current_section:
        return {}

    temperature = _first_number(_get_text(current_section.select_one(".weather .degree .number")))
    condition_raw = _get_text(current_section.select_one(".weather-description"))
    if not condition_raw:
        condition_raw = _get_attr(current_section.select_one(".icon-weather img"), "alt")

    current: dict[str, Any] = {
        "temperature": temperature,
        "condition_raw": condition_raw,
        "time": _get_text(current_section.select_one(".time")),
        "date": _get_text(current_section.select_one(".date")),
    }

    for item in current_section.select(".additional-info .item"):
        icon_src = _get_attr(item.select_one(".sign img"), "src") or ""
        value_text = _get_text(item.select_one(".text"))
        if "thermometer" in icon_src:
            current["temperature"] = _first_number(value_text)
        elif "raindrop" in icon_src:
            current["humidity"] = _first_int(value_text)
        elif "pressure" in icon_src:
            current["pressure"] = _first_int(value_text)
        elif "wind" in icon_src:
            current["wind_speed"] = _first_number(value_text)

    return current


def _parse_hourly(city_wrap: Any) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for item in city_wrap.select(".box-hourly li.forecast"):
        hour = _get_text(item.select_one(".hour"))
        temp = _first_number(_get_text(item.select_one(".degree .number")))
        icon = item.select_one(".icon-forecast img")
        condition_raw = _get_attr(icon, "title") or _get_attr(icon, "alt")
        results.append(
            {
                "hour": hour,
                "temperature": temp,
                "condition_raw": condition_raw,
            }
        )
    return results


def _parse_daily(city_wrap: Any) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for row in city_wrap.select(".box-daily .daily-forecast .row"):
        label = _get_text(row.select_one(".day"))
        icon = row.select_one(".icon-forecast img")
        condition_raw = _get_attr(icon, "title") or _get_attr(icon, "alt")
        degrees = [
            _get_text(node)
            for node in row.select(".min-max-degree .degree .number")
            if _get_text(node)
        ]
        temp_low = _first_number(degrees[0]) if len(degrees) > 0 else None
        temp_high = _first_number(degrees[1]) if len(degrees) > 1 else None
        details = _parse_details(row.select_one(".box-information"))
        results.append(
            {
                "label": label,
                "condition_raw": condition_raw,
                "temperature_low": temp_low,
                "temperature_high": temp_high,
                "details": details,
            }
        )
    return results


def _parse_details(info_box: Any) -> dict[str, Any]:
    if not info_box:
        return {}

    details: dict[str, Any] = {}
    for item in info_box.select("li"):
        name_node = item.select_one(".name")
        if not name_node:
            continue
        name = _get_text(name_node).lower()
        value = _get_text(item).replace(_get_text(name_node), "", 1).strip()
        if "усеща" in name:
            details["feels_like"] = _first_number(value)
        elif "скорост" in name and "вят" in name:
            details["wind_speed"] = _first_number(value)
        elif "посока" in name and "вят" in name:
            details["wind_direction"] = value
        elif "наляган" in name:
            details["pressure"] = _first_int(value)
        elif "влажност" in name:
            details["humidity"] = _first_int(value)
        elif "температура" in name:
            details["temperature_range"] = value

    return details


def _get_text(node: Any) -> str:
    if not node:
        return ""
    return node.get_text(" ", strip=True)


def _get_attr(node: Any, name: str) -> str:
    if not node:
        return ""
    return node.get(name, "")


def _first_number(value: str) -> float | None:
    if not value:
        return None
    match = re.search(r"-?\d+(?:[\.,]\d+)?", value)
    if not match:
        return None
    return float(match.group(0).replace(",", "."))


def _first_int(value: str) -> int | None:
    number = _first_number(value)
    if number is None:
        return None
    return int(round(number))
