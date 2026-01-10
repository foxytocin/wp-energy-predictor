from homeassistant import config_entries
import voluptuous as vol
from .const import CONF_SENSOR, DOMAIN

class OptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        sensors = [
            entity_id for entity_id in self.hass.states.entity_ids()
            if entity_id.startswith("sensor.") and "energy" in entity_id
        ]

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_SENSOR, default=self.entry.options.get(CONF_SENSOR, self.entry.data[CONF_SENSOR])): vol.In(sensors)
        })

        return self.async_show_form(step_id="init", data_schema=schema)