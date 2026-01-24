"""Weather entity for BG Vremeto."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any

from homeassistant.components.weather import WeatherEntity, WeatherEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util
from homeassistant.const import UnitOfLength, UnitOfPressure, UnitOfSpeed, UnitOfTemperature

from .const import (
    ATTR_CONDITION_RAW,
    ATTR_OBSERVED_DATE,
    ATTR_OBSERVED_TIME,
    ATTR_WIND_DIRECTION,
    CONF_LOCATION,
    CONF_NAME,
    CONF_PROVIDER,
    DOMAIN,
)
from .coordinator import BGVremetoDataUpdateCoordinator


@dataclass
class _ForecastEntry:
    datetime: datetime | None
    temperature: float | None
    templow: float | None = None
    condition: str | None = None
    wind_speed: float | None = None
    wind_bearing: int | None = None
    humidity: int | None = None
    pressure: int | None = None


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up BG Vremeto weather from a config entry."""
    coordinator: BGVremetoDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BGVremetoWeatherEntity(coordinator, entry)])


class BGVremetoWeatherEntity(CoordinatorEntity[BGVremetoDataUpdateCoordinator], WeatherEntity):
    """Representation of BG Vremeto weather."""

    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_native_visibility_unit = UnitOfLength.METERS
    _attr_attribution = "Data from dalivali.bg and sinoptik.bg"

    def __init__(self, coordinator: BGVremetoDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = entry.unique_id or entry.entry_id
        name = entry.data.get(CONF_NAME)
        if name:
            self._attr_name = name
        else:
            self._attr_name = coordinator.data.get("city") or "BG Vremeto"

    @property
    def condition(self) -> str | None:
        return _map_condition(self.coordinator.data.get("current", {}).get("condition_raw"))

    @property
    def native_temperature(self) -> float | None:
        return self.coordinator.data.get("current", {}).get("temperature")

    @property
    def temperature(self) -> float | None:
        return self.native_temperature

    @property
    def humidity(self) -> int | None:
        return self.coordinator.data.get("current", {}).get("humidity")

    @property
    def native_pressure(self) -> float | None:
        return self.coordinator.data.get("current", {}).get("pressure")

    @property
    def pressure(self) -> float | None:
        return self.native_pressure

    @property
    def native_wind_speed(self) -> float | None:
        return self.coordinator.data.get("current", {}).get("wind_speed")

    @property
    def wind_speed(self) -> float | None:
        return self.native_wind_speed

    @property
    def wind_bearing(self) -> int | None:
        direction = self._wind_direction_text()
        return _wind_direction_to_bearing(direction)

    @property
    def apparent_temperature(self) -> float | None:
        current = self.coordinator.data.get("current", {})
        return current.get("feels_like") or self._today_details().get("feels_like")

    @property
    def native_apparent_temperature(self) -> float | None:
        return self.apparent_temperature

    @property
    def native_visibility(self) -> float | None:
        return self.coordinator.data.get("current", {}).get("visibility")

    @property
    def visibility(self) -> float | None:
        return self.native_visibility

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        current = self.coordinator.data.get("current", {})
        attrs: dict[str, Any] = {
            ATTR_CONDITION_RAW: current.get("condition_raw"),
            ATTR_OBSERVED_TIME: current.get("time"),
            ATTR_OBSERVED_DATE: current.get("date"),
            ATTR_WIND_DIRECTION: self._wind_direction_text(),
            "feels_like": current.get("feels_like")
            or self._today_details().get("feels_like"),
            "city": self.coordinator.data.get("city"),
            "location": self._entry.data.get(CONF_LOCATION),
            "provider": self._entry.data.get(CONF_PROVIDER),
            "precipitation_probability": current.get("precipitation_probability"),
            "precipitation_amount": current.get("precipitation_amount"),
            "storm_probability": current.get("storm_probability"),
            "cloudiness": current.get("cloudiness"),
            "uv_index": current.get("uv_index"),
            "visibility": current.get("visibility"),
        }
        return {key: value for key, value in attrs.items() if value not in (None, "")}

    async def async_forecast_daily(self):
        return [_clean_forecast(entry.__dict__) for entry in _build_daily_forecast(self.coordinator.data)]

    async def async_forecast_hourly(self):
        return [_clean_forecast(entry.__dict__) for entry in _build_hourly_forecast(self.coordinator.data)]

    @property
    def forecast(self):
        return [_clean_forecast(entry.__dict__) for entry in _build_daily_forecast(self.coordinator.data)]

    def _wind_direction_text(self) -> str | None:
        current = self.coordinator.data.get("current", {})
        if current.get("wind_direction"):
            return current.get("wind_direction")
        return self._today_details().get("wind_direction")

    def _today_details(self) -> dict[str, Any]:
        for item in self.coordinator.data.get("daily", []):
            label = (item.get("label") or "").strip().lower()
            if label == "днес":
                return item.get("details", {})
        return {}


def _build_hourly_forecast(data: dict[str, Any]) -> list[_ForecastEntry]:
    now = dt_util.now()
    last_dt: datetime | None = None
    forecasts: list[_ForecastEntry] = []

    for item in data.get("hourly", []):
        hour_text = (item.get("hour") or "").strip()
        if not hour_text:
            continue

        if hour_text.lower() == "сега":
            forecast_dt = now
        else:
            try:
                if ":" in hour_text:
                    hour, minute = hour_text.split(":", 1)
                    hour = int(hour)
                    minute = int(minute)
                else:
                    hour = int(hour_text)
                    minute = 0
            except ValueError:
                forecast_dt = None
            else:
                forecast_dt = now.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )

        if forecast_dt and last_dt and forecast_dt <= last_dt:
            while forecast_dt <= last_dt:
                forecast_dt += timedelta(days=1)
        elif forecast_dt and forecast_dt < now:
            forecast_dt += timedelta(days=1)

        if forecast_dt:
            last_dt = forecast_dt

        forecasts.append(
            _ForecastEntry(
                datetime=forecast_dt,
                temperature=item.get("temperature"),
                condition=_map_condition(item.get("condition_raw")),
                wind_speed=item.get("wind_speed"),
                wind_bearing=_wind_direction_to_bearing(item.get("wind_direction")),
                humidity=item.get("humidity"),
                pressure=item.get("pressure"),
            )
        )

    return forecasts


def _build_daily_forecast(data: dict[str, Any]) -> list[_ForecastEntry]:
    now = dt_util.now()
    today = now.date()
    tzinfo = now.tzinfo
    last_date: date | None = None
    forecasts: list[_ForecastEntry] = []

    for item in data.get("daily", []):
        label = (item.get("label") or "").strip()
        forecast_date = _resolve_day_label(label, today, last_date)
        if forecast_date:
            last_date = forecast_date
        forecasts.append(
            _ForecastEntry(
                datetime=datetime.combine(forecast_date, time.min, tzinfo=tzinfo)
                if forecast_date
                else None,
                temperature=item.get("temperature_high"),
                templow=item.get("temperature_low"),
                condition=_map_condition(item.get("condition_raw")),
                wind_speed=item.get("details", {}).get("wind_speed"),
                wind_bearing=_wind_direction_to_bearing(
                    item.get("details", {}).get("wind_direction")
                ),
                humidity=item.get("details", {}).get("humidity"),
                pressure=item.get("details", {}).get("pressure"),
            )
        )

    return forecasts


def _resolve_day_label(label: str, today: date, last_date: date | None) -> date | None:
    lower = label.lower()
    if lower == "днес":
        return today
    if lower == "утре":
        return today + timedelta(days=1)

    weekday_map = {
        "понеделник": 0,
        "вторник": 1,
        "сряда": 2,
        "четвъртък": 3,
        "петък": 4,
        "събота": 5,
        "неделя": 6,
    }
    weekday = weekday_map.get(lower)
    if weekday is None:
        return None

    base = last_date or today
    days_ahead = (weekday - base.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    return base + timedelta(days=days_ahead)


def _wind_direction_to_bearing(direction: str | None) -> int | None:
    if not direction:
        return None
    key = direction.strip().lower()
    mapping = {
        "север": 0,
        "североизток": 45,
        "изток": 90,
        "югоизток": 135,
        "юг": 180,
        "югозапад": 225,
        "запад": 270,
        "северозапад": 315,
    }
    return mapping.get(key)


def _map_condition(raw: str | None) -> str | None:
    if not raw:
        return None
    text = raw.strip().lower()

    if "гръмот" in text:
        if "дъжд" in text or "валеж" in text:
            return "lightning_rainy"
        return "lightning"
    if "градуш" in text:
        return "hail"
    if "сняг" in text or "снеж" in text:
        if "дъжд" in text:
            return "snowy_rainy"
        return "snowy"
    if "мъг" in text:
        return "fog"
    if "дъжд" in text or "валеж" in text:
        if "силен" in text or "пролив" in text:
            return "pouring"
        return "rainy"
    if "вят" in text:
        return "windy"
    if "разкъсан" in text or "незначителна облачност" in text or "променлива" in text:
        return "partlycloudy"
    if "предимно" in text and ("облачно" in text or "слънч" in text):
        return "partlycloudy"
    if "облачно" in text:
        return "cloudy"
    if "слънч" in text or "ясно" in text:
        return "sunny"

    return None


def _clean_forecast(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}
