"""HTML parsing helpers for Sinoptik.bg weather data."""
from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup


WIND_DIRECTION_MAP = {
    "windimge": "изток",
    "windimgse": "югоизток",
    "windimgs": "юг",
    "windimgsw": "югозапад",
    "windimgw": "запад",
    "windimgnw": "северозапад",
    "windimgn": "север",
    "windimgne": "североизток",
    "windimgtope": "изток",
    "windimgtopse": "югоизток",
    "windimgtops": "юг",
    "windimgtopsw": "югозапад",
    "windimgtopw": "запад",
    "windimgtopnw": "северозапад",
    "windimgtopn": "север",
    "windimgtopne": "североизток",
}


def parse_sinoptik_html(
    current_html: str, hourly_html: str, daily_html: str
) -> dict[str, Any]:
    """Parse Sinoptik HTML into structured weather data."""
    current_soup = BeautifulSoup(current_html, "html.parser")
    hourly_soup = BeautifulSoup(hourly_html, "html.parser")
    daily_soup = BeautifulSoup(daily_html, "html.parser")

    city = _get_text(current_soup.select_one("h1.currentCity"))
    if not city:
        city = _get_text(daily_soup.select_one("h1.currentCity"))

    return {
        "city": city,
        "current": _parse_current(current_soup),
        "hourly": _parse_hourly(hourly_soup),
        "daily": _parse_daily(daily_soup),
    }


def _parse_current(soup: BeautifulSoup) -> dict[str, Any]:
    current: dict[str, Any] = {}

    current["temperature"] = _first_number(
        _get_text(soup.select_one(".wfCurrentTemp"))
    )
    current["condition_raw"] = _get_text(
        soup.select_one(".wfCurrentWindContainer strong")
    )
    current["feels_like"] = _first_number(
        _get_text(soup.select_one(".wfCurrentFeelTemp span"))
    )

    wind_node = soup.select_one(".wfCurrentWind")
    current["wind_speed"] = _first_number(_get_text(wind_node))
    current["wind_direction"] = _wind_direction_from_node(wind_node)

    for wrapper in soup.select(".wfCurrentWrapper"):
        heading = _get_text(wrapper.select_one(".wfCurrentHeading")).lower()
        value = _get_text(wrapper.select_one(".wfCurrentValue"))
        if not heading:
            continue
        if "вероятност за валежи" in heading:
            current["precipitation_probability"] = _first_int(value)
        elif "количество валежи" in heading:
            current["precipitation_amount"] = _first_number(value)
        elif "вероятност за буря" in heading:
            current["storm_probability"] = _first_int(value)
        if "наляган" in heading:
            current["pressure"] = _first_int(value)
        elif "влажност" in heading:
            current["humidity"] = _first_int(value)
        elif "облачност" in heading:
            current["cloudiness"] = _first_int(value)
        elif "uv индекс" in heading:
            current["uv_index"] = _first_number(value)
        elif "видимост" in heading:
            current["visibility"] = _parse_distance_meters(value)

    return {key: value for key, value in current.items() if value not in (None, "")}


def _parse_hourly(soup: BeautifulSoup) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for item in soup.select("#wfTabHourlyContentSlide .wfByHour"):
        hour = _get_text(item.select_one(".wfByHourHour"))
        temp_node = _find_first(item.select(".wfByHourTemp"), "wfByHourFeelsLike")
        condition = _get_text(item.select_one(".wfByHourCond"))
        wind_node = item.select_one(".wfByHourWind")
        wind_icon = item.select_one(".wfByHourWind span[class*='windImg']")
        add_values = item.select(".wfHourlyAddValue")

        pressure = _first_int(_get_text(add_values[3])) if len(add_values) > 3 else None
        humidity = _first_int(_get_text(add_values[4])) if len(add_values) > 4 else None

        results.append(
            {
                "hour": hour,
                "temperature": _first_number(_get_text(temp_node)),
                "condition_raw": condition,
                "wind_speed": _first_number(_get_text(wind_node)),
                "wind_direction": _wind_direction_from_node(wind_icon or wind_node),
                "pressure": pressure,
                "humidity": humidity,
            }
        )

    return results


def _parse_daily(soup: BeautifulSoup) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for item in soup.select(".wf5dayRight"):
        label = _get_text(item.select_one(".wf5dayRightDay"))
        condition = _get_text(item.select_one(".wf5dayRightCond"))
        temp_text = _get_text(item.select_one(".wf5dayRightTemp"))
        numbers = _all_numbers(temp_text)
        temp_low = numbers[0] if len(numbers) > 0 else None
        temp_high = numbers[1] if len(numbers) > 1 else None

        wind_node = item.select_one(".wf5dayRightWind")
        wind_speed = _first_number(_get_text(wind_node))
        wind_direction = _wind_direction_from_node(
            item.select_one(".wf5dayRightWind .wind-img") or wind_node
        )

        details = {
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
        }

        results.append(
            {
                "label": label,
                "condition_raw": condition,
                "temperature_low": temp_low,
                "temperature_high": temp_high,
                "details": {key: value for key, value in details.items() if value is not None},
            }
        )

    return results


def _wind_direction_from_node(node: Any) -> str | None:
    if not node:
        return None
    classes = node.get("class", []) if hasattr(node, "get") else []
    for class_name in classes:
        key = class_name.lower()
        if key in WIND_DIRECTION_MAP:
            return WIND_DIRECTION_MAP[key]
    return None


def _find_first(nodes: list[Any], skip_class: str) -> Any:
    for node in nodes:
        classes = node.get("class", []) if hasattr(node, "get") else []
        if skip_class not in classes:
            return node
    return None


def _get_text(node: Any) -> str:
    if not node:
        return ""
    return node.get_text(" ", strip=True)


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


def _all_numbers(value: str) -> list[float]:
    if not value:
        return []
    numbers = re.findall(r"-?\d+(?:[\.,]\d+)?", value)
    return [float(number.replace(",", ".")) for number in numbers]


def _parse_distance_meters(value: str) -> float | None:
    if not value:
        return None
    number = _first_number(value)
    if number is None:
        return None
    lower = value.lower()
    if "km" in lower:
        return number * 1000.0
    return number
