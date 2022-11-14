"""Constants for the HT3 integration."""

from homeassistant.const import (
    PERCENTAGE,
    TEMP_CELSIUS,
)
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.binary_sensor import BinarySensorDeviceClass

DOMAIN = "junkers_ht3"
KEY_GATEWAY = "ht3_gateway"
EVENT = "ht3_event"

MANUFACTURER = "Junkers"
DEVICE_NAME = "Heatronic 3"
DEVICE_MODEL = "HT3 gateway"
DEVICE_SW_VERSION = "v1.0"

SERVICE_RECONNECT = "reconnect"

BINARY_SENSOR_DICT = {
    "ch_burner_operation": ["Burner operation", "mdi:fire", ""],
    "dhw_Tok": ["DHW OK", "mdi:water-check", BinarySensorDeviceClass.HEAT],
    "dhw_generating": ["DHW generating", "mdi:water-boiler", ""],
    "ch_pump_heating": ["Pump Heating", "mdi:sync", ""],
}

BINARY_SENSOR_LIST = list(BINARY_SENSOR_DICT)

SENSOR_DICT = {
    "ch_Tflow_measured": [
        "CH Temp flow measured",
        TEMP_CELSIUS,
        "mdi:radiator",
        SensorDeviceClass.TEMPERATURE,
    ],
    "ch_burner_power": [
        "CH Burner power",
        PERCENTAGE,
        "mdi:gauge",
        SensorDeviceClass.POWER_FACTOR,
    ],
    "ch_Tflow_desired": [
        "CH Temp flow desired",
        TEMP_CELSIUS,
        "mdi:radiator",
        SensorDeviceClass.TEMPERATURE,
    ],
    "hc_Tdesired": [
        "HC Temp desired",
        TEMP_CELSIUS,
        "mdi:home-thermometer",
        SensorDeviceClass.TEMPERATURE,
    ],
    "hc_Tmeasured": [
        "HC Temp measured",
        TEMP_CELSIUS,
        "mdi:home-thermometer",
        SensorDeviceClass.TEMPERATURE,
    ],
    "dhw_Tdesired": [
        "DHW Temp desired",
        TEMP_CELSIUS,
        "mdi:shower",
        SensorDeviceClass.TEMPERATURE,
    ],
    "dhw_Tmeasured": [
        "DHW Temp measured",
        TEMP_CELSIUS,
        "mdi:shower",
        SensorDeviceClass.TEMPERATURE,
    ],
}

SENSOR_LIST = list(SENSOR_DICT)
