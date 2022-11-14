"""Config flow to configure component."""
from __future__ import annotations
import voluptuous as vol

from typing import Any

# from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_HOST, CONF_PORT
import homeassistant.helpers.config_validation as cv
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .driver import Ht3Driver


class Ht3FlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for HT3 platform."""

    VERSION = 1
    # CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def _show_setup_form(
        self, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=8088): vol.Coerce(int),
                }
            ),
            errors=errors or {},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        if user_input is None:
            return await self._show_setup_form(user_input)

        self._async_abort_entries_match(
            {CONF_HOST: user_input[CONF_HOST], CONF_PORT: user_input[CONF_PORT]}
        )

        await self.async_set_unique_id(user_input[CONF_HOST])
        self._abort_if_unique_id_configured()

        errors = {}

        driver = Ht3Driver(user_input[CONF_HOST], port=user_input[CONF_PORT])

        driver.connect()
        if not driver.connected():
            errors["base"] = "cannot_connect"
            return await self._show_setup_form(errors)

        return self.async_create_entry(
            title=user_input[CONF_HOST],
            data={
                CONF_HOST: user_input[CONF_HOST],
                CONF_PORT: user_input[CONF_PORT],
            },
        )

    async def _show_config_form(
        self, host=None, port=None, username=None, password=None
    ):
        """Show the configuration form to edit HT3 data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=host): str,
                    vol.Required(CONF_PORT, default=port): cv.port,
                }
            ),
            errors="",  # self._errors,
        )
