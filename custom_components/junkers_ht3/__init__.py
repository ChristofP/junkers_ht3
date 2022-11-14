"""Junkers Heatronic 3 integration"""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv

# from homeassistant.helpers.discovery import load_platform
# from homeassistant.helpers import entity_platform, service
# from homeassistant.helpers import device_registry
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.const import EVENT_HOMEASSISTANT_START, EVENT_HOMEASSISTANT_STOP

from .const import DOMAIN, KEY_GATEWAY, EVENT, SERVICE_RECONNECT, MANUFACTURER

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_PORT): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Set up the Heatronic parent component."""
    _LOGGER.info("Creating new Heatronic component")

    conf = config.get(DOMAIN)

    if conf is None:
        return True

    host = conf.get(CONF_HOST)
    port = conf.get(CONF_PORT)

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={CONF_HOST: host, CONF_PORT: port},
        )
    )

    return True


async def async_setup_entry(hass, entry):
    from .driver import Ht3Driver

    driver = Ht3Driver(entry.data[CONF_HOST], entry.data[CONF_PORT])

    async def start_ht3_driver(self):
        driver.start()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, start_ht3_driver)

    async def stop_ht3_client(self):
        """Close connection when hass stops."""
        driver.stop()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_ht3_client)

    hass.data.setdefault(KEY_GATEWAY, {})[entry.entry_id] = driver

    def handle_value_changed(name, value):
        hass.bus.fire(EVENT, {"name": name, "value": value})

    driver.set_callback(handle_value_changed)

    _LOGGER.info("Connected to HT3 bus")

    # Start climate component
    _LOGGER.debug("Starting climate/sensor components")
    # load_platform(hass, 'climate', DOMAIN, {}, config)
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "climate")
    )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "binary_sensor")
    )

    # device registry
    # dr = device_registry.async_get(hass)
    # dr.async_get_or_create(
    #     config_entry_id=entry.entry_id,
    #     connections=set(),
    #     identifiers={(DOMAIN, entry.data[CONF_HOST])},
    #     manufacturer=MANUFACTURER,
    #     name="Heatronic 3",
    #     model="HT3 gateway",
    #     sw_version="v1.0",
    # )

    # service registry
    async def async_reconnect(self):
        _LOGGER.info("Reconnect to HT3 bus")
        driver.stop()
        # driver = Ht3Driver(entry.data[CONF_HOST], entry.data[CONF_PORT])
        driver.restart()

    hass.services.async_register(DOMAIN, SERVICE_RECONNECT, async_reconnect)

    return True
