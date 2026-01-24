# BG Vremeto (Home Assistant)

Custom Home Assistant integration that parses weather data from dalivali.bg and sinoptik.bg.

## Features
- Current conditions (temperature, humidity, pressure, wind, feels-like)
- Hourly forecast (provider-specific page)
- Daily forecast (10-day for DaliVali, 5-day for Sinoptik)
- Provider selection per config entry
- Configurable update interval
- Extra attributes from Sinoptik (precipitation chances, UV index, visibility, cloudiness)

## Installation

### HACS
1. Add this repository to HACS as a custom repository (Integration).
2. Install **BG Vremeto** from HACS.
3. Restart Home Assistant.
4. Add the integration from Settings -> Devices & Services.

### Manual
1. Copy `custom_components/bg_vremeto` into your Home Assistant `custom_components` folder.
2. Restart Home Assistant.
3. Add the integration from Settings -> Devices & Services.

## Configuration
Configuration is done via the UI.

- **Provider**: DaliVali or Sinoptik.
- **Location**: numeric ID for DaliVali (e.g. `217`), or slug for Sinoptik (e.g. `sofia-bulgaria-100727011`).
- **Name** (optional): entity name override.
- **Update interval** (seconds): polling interval, default 600 seconds.

### How to find a location ID
Open https://www.dalivali.bg/ and search for your city. The URL will include `?location=XXX`.
Open https://www.sinoptik.bg/ and search for your city. The URL path includes the slug you need.

## State attributes
Depending on the provider, the weather entity exposes extra state attributes such as:
- `feels_like`
- `precipitation_probability`
- `precipitation_amount`
- `storm_probability`
- `cloudiness`
- `uv_index`
- `visibility` (meters)

## Notes
- This integration scrapes HTML. If the site changes its structure, parsing may break.
- Data sources: https://www.dalivali.bg/ and https://www.sinoptik.bg/

## Support
Open an issue in this repository with logs, provider, and the location used.
