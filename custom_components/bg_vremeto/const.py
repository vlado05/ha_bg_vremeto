"""Constants for the BG Vremeto weather integration."""
from datetime import timedelta

DOMAIN = "bg_vremeto"
PLATFORMS = ["weather"]

CONF_PROVIDER = "provider"
CONF_LOCATION = "location"
CONF_NAME = "name"
CONF_SCAN_INTERVAL = "scan_interval"

PROVIDER_DALIVALI = "dalivali"
PROVIDER_SINOPTIK = "sinoptik"

PROVIDERS = {
    PROVIDER_DALIVALI: "DaliVali",
    PROVIDER_SINOPTIK: "Sinoptik.bg",
}

DEFAULT_NAME = "BG Vremeto"
DEFAULT_PROVIDER = PROVIDER_DALIVALI
DEFAULT_SCAN_INTERVAL = timedelta(minutes=10)

ATTR_CONDITION_RAW = "condition_raw"
ATTR_OBSERVED_TIME = "observed_time"
ATTR_OBSERVED_DATE = "observed_date"
ATTR_WIND_DIRECTION = "wind_direction"
