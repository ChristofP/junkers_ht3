"""Support for sensors."""
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    BINARY_SENSOR_DICT,
    BINARY_SENSOR_LIST,
    MANUFACTURER,
    DOMAIN,
    EVENT,
    DEVICE_NAME,
    DEVICE_MODEL,
    DEVICE_SW_VERSION,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the HT3 sensor."""
    sensors = [
        Ht3BinarySensor(
            hass=hass,
            resource=sensor_name,
            entry_id=config_entry.entry_id,
        )
        for sensor_name in BINARY_SENSOR_LIST
    ]
    async_add_entities(sensors, True)


class Ht3BinarySensor(BinarySensorEntity):
    """Representation of a Sensor."""

    def __init__(self, hass, resource, entry_id):
        """Initialize the sensor."""
        variable_info = BINARY_SENSOR_DICT[resource]
        self._state = False
        self._name = variable_info[0] if variable_info[0] else resource
        self._resource = resource
        self._entry_id = entry_id

        # self._name = variable_info[0]
        self._device_class = variable_info[2]
        self._icon = variable_info[1]

        self._available = False

        hass.bus.async_listen(EVENT, self._handle_code)

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._resource}"

    @property
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information of the entity."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": DEVICE_NAME,
            "manufacturer": MANUFACTURER,
            "model": DEVICE_MODEL,
            "sw_version": DEVICE_SW_VERSION,
        }

    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        return False

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return True if the binary sensor is on."""
        return self._state

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    def _handle_code(self, call):
        """Handle received code by the ht3-daemon.
        If the code matches the defined payload
        of this sensor the sensor state is changed accordingly.
        """
        # Check if received code matches defined payload
        # True if payload is contained in received code dict, not
        # all items have to match
        if self._resource == call.data.get("name"):
            try:
                value = call.data["value"]
                self._state = True if value == 1 else False
                self._available = True
                self.async_schedule_update_ha_state(False)
            except KeyError:
                _LOGGER.error(
                    "No variable %s in received code data %s",
                    str(self._resource),
                    str(call.data),
                )
                self._available = False
