"""Support for MQTT climate devices."""
import logging
from typing import Any

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    PRESET_AWAY,
    PRESET_NONE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_WHOLE,
)

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .driver import Ht3Driver

from .const import (
    DOMAIN,
    EVENT,
    KEY_GATEWAY,
    MANUFACTURER,
    DEVICE_NAME,
    DEVICE_MODEL,
    DEVICE_SW_VERSION,
)

_LOGGER = logging.getLogger(__name__)

KEY_ENTITY = "ht3_climate"

PRESET_COMFORT = "Comfort"
PRESET_ECO = "Eco"
PRESET_FROST = "Frost"

ATTR_CONNECTED = "Connected"
ATTR_CLIENT_ID = "Client ID"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Load NHC2 lights based on a config entry."""
    hass.data.setdefault(KEY_ENTITY, {})[config_entry.entry_id] = []
    driver: Ht3Driver = hass.data[KEY_GATEWAY][config_entry.entry_id]
    _LOGGER.debug("Platform is starting")
    async_add_entities(
        [Ht3Climate(hass=hass, driver=driver, config_entry_id=config_entry.entry_id)]
    )


class Ht3Climate(ClimateEntity):
    """Representation of an MQTT climate device."""

    def __init__(self, hass, driver: Ht3Driver, config_entry_id):
        """Initialize the climate device."""
        # self._unique_id = config.get(CONF_UNIQUE_ID)
        self._sub_state = None

        self.hass = hass
        self.driver = driver
        self._config_entry_id = config_entry_id
        self._action = None
        self._current_operation = HVACMode.OFF
        self._current_temp = None
        self._target_temp = None
        self._preset = None
        self._auto = False
        self._unit_of_measurement = hass.config.units.temperature_unit
        self._value_templates = None
        self._away = False
        self._hold = False

        hass.bus.async_listen(EVENT, self._handle_code)

    # async def async_will_remove_from_hass(self):
    #     """Unsubscribe when removed."""
    #     self._sub_state = await subscription.async_unsubscribe_topics(
    #         self.hass, self._sub_state
    #     )
    #     await MqttAttributes.async_will_remove_from_hass(self)
    #     await MqttAvailability.async_will_remove_from_hass(self)

    def _handle_code(self, call):
        """Handle received code by the ht3-daemon.
        If the code matches the defined payload
        of this sensor the sensor state is changed accordingly.
        """
        # Check if received code matches defined payload
        # True if payload is contained in received code dict, not
        # all items have to match
        if "hc_Tdesired" == call.data.get("name"):
            try:
                value = call.data["value"]
                self._target_temp = value
                self.schedule_update_ha_state()
            except KeyError:
                _LOGGER.error(
                    "No variable 'hc_Tdesired' in received code data %s",
                    str(call.data),
                )
        elif "hc_Tmeasured" == call.data.get("name"):
            try:
                value = call.data["value"]
                self._current_temp = value
                self.schedule_update_ha_state()
            except KeyError:
                _LOGGER.error(
                    "No variable 'hc_Tmeasured' in received code data %s",
                    str(call.data),
                )
        elif "hc_mode" == call.data.get("name"):
            try:
                value = call.data["value"]
                if value == 1:
                    self._current_operation = (
                        HVACMode.OFF if not self._auto else HVACMode.AUTO
                    )
                    self._preset = PRESET_FROST
                elif value == 2:
                    self._current_operation = (
                        HVACMode.OFF if not self._auto else HVACMode.AUTO
                    )
                    self._preset = PRESET_ECO
                elif value == 3:
                    self._current_operation = (
                        HVACMode.HEAT if not self._auto else HVACMode.AUTO
                    )
                    self._preset = PRESET_COMFORT
                elif value == 4:
                    self._current_operation = HVACMode.AUTO
                else:
                    self._current_operation = HVACMode.OFF
                    self._preset = PRESET_NONE
                self.schedule_update_ha_state()
            except KeyError:
                _LOGGER.error(
                    "No variable 'hc_mode' in received code data %s",
                    str(call.data),
                )
        elif "hc_auto" == call.data.get("name"):
            try:
                value = call.data["value"]
                if value == 1:
                    self._auto = False
                else:  # value == 2
                    self._auto = True
                self.schedule_update_ha_state()
            except KeyError:
                _LOGGER.error(
                    "No variable 'hc_auto' in received code data %s",
                    str(call.data),
                )

    @property
    def should_poll(self) -> bool:
        """Return the polling state."""
        return False

    @property
    def name(self) -> str:
        """Return the name of the climate device."""
        return "ht3"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._config_entry_id}/{self.name}"

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def current_temperature(self) -> float:
        """Return the current temperature."""
        return self._current_temp

    @property
    def target_temperature(self) -> float:
        """Return the temperature we try to reach."""
        return self._target_temp

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current running hvac operation if supported."""
        return self._action

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current operation ie. heat, cool, idle."""
        return self._current_operation

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available operation modes."""
        # return [HVAC_MODE_AUTO, HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_OFF]
        return [HVACMode.HEAT, HVACMode.OFF]

    @property
    def target_temperature_step(self) -> float:
        """Return the supported step of target temperature."""
        return PRECISION_WHOLE  # PRECISION_HALVES

    @property
    def preset_mode(self) -> str:
        """Return preset mode."""
        return self._preset

    @property
    def preset_modes(self) -> list[str]:
        """Return preset modes."""
        presets = [PRESET_COMFORT, PRESET_ECO, PRESET_FROST]
        return presets

    @property
    def available(self) -> bool:
        """Return if the device is available."""
        return self.driver.connected()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperatures."""
        if kwargs.get(ATTR_HVAC_MODE) is not None:
            operation_mode = kwargs.get(ATTR_HVAC_MODE)
            await self.async_set_hvac_mode(operation_mode)

        self.driver.write_hc_trequested(kwargs.get(ATTR_TEMPERATURE))
        # self._target_temp = kwargs.get(ATTR_TEMPERATURE) //will be set with update from thermostat

        # Always optimistic?
        # self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new operation mode."""
        if hvac_mode == HVACMode.OFF:
            self.driver.write_hc_mode(2)  # 1
        elif hvac_mode == HVACMode.COOL:
            self.driver.write_hc_mode(2)
        elif hvac_mode == HVACMode.HEAT:
            self.driver.write_hc_mode(3)
        elif hvac_mode == HVACMode.AUTO:
            self.driver.write_hc_mode(4)

        # self._current_operation = hvac_mode //will be set with update from thermostat
        # self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set a preset mode."""
        if preset_mode == self.preset_mode:
            return

        # Track if we should optimistic update the state
        optimistic_update = False

        if self._away:
            optimistic_update = optimistic_update or self._set_away_mode(False)
        elif preset_mode == PRESET_AWAY:
            if self._hold:
                self._set_hold_mode(None)
            optimistic_update = optimistic_update or self._set_away_mode(True)
        else:
            hold_mode = preset_mode
            if preset_mode == PRESET_NONE:
                hold_mode = None
            optimistic_update = optimistic_update or self._set_hold_mode(hold_mode)

        if optimistic_update:
            self.async_write_ha_state()

    def _set_away_mode(self, state):
        """Set away mode.

        Returns if we should optimistically write the state.
        """
        self._away = state
        return True

    def _set_hold_mode(self, hold_mode):
        """Set hold mode.

        Returns if we should optimistically write the state.
        """
        self._hold = hold_mode
        return True

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        support = 0
        support |= ClimateEntityFeature.TARGET_TEMPERATURE
        # support |= SUPPORT_PRESET_MODE

        return support

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return 5  # self._config[CONF_TEMP_MIN]

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return 30  # self._config[CONF_TEMP_MAX]

    @property
    def precision(self) -> float:
        """Return the precision of the system."""
        # if self._config.get(CONF_PRECISION) is not None:
        #    return self._config.get(CONF_PRECISION)
        return super().precision

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information of the entity."""
        return {
            "identifiers": {(DOMAIN, self._config_entry_id)},
            "name": DEVICE_NAME,
            "manufacturer": MANUFACTURER,
            "model": DEVICE_MODEL,
            "sw_version": DEVICE_SW_VERSION,
        }

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return {
            ATTR_CONNECTED: self.driver.connected(),
            ATTR_CLIENT_ID: self.driver.clientID(),
        }
