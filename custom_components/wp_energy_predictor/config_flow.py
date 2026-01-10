from homeassistant import config_entries
import voluptuous as vol

from .const import DOMAIN, CONF_SENSOR


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="WP Energy Predictor", data=user_input)

        sensors = [
            entity_id for entity_id in self.hass.states.entity_ids()
            if entity_id.startswith("sensor.") and "energy" in entity_id
        ]

        schema = vol.Schema({
            vol.Required(CONF_SENSOR): vol.In(sensors)
        })

        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    def async_get_options_flow(entry):
        return OptionsFlow(entry)


class OptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        return self.async_show_form(step_id="init")