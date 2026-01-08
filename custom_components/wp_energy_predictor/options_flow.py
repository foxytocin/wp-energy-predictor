import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.entity_registry import async_get
from .const import DOMAIN, CONF_SENSOR

class WPEnergyPredictorOptionsFlow(config_entries.OptionsFlow):

    def __init__(self, config_entry):
        self.entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        registry = async_get(self.hass)
        sensors = [
            ent.entity_id
            for ent in registry.entities.values()
            if ent.entity_id.startswith("sensor.")
        ]

        current = self.entry.options.get(
            CONF_SENSOR,
            self.entry.data.get(CONF_SENSOR)
        )

        schema = vol.Schema({
            vol.Required(CONF_SENSOR, default=current): vol.In(sorted(sensors))
        })

        return self.async_show_form(step_id="init", data_schema=schema)