import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.entity_registry import async_get

from .const import DOMAIN, CONF_SENSOR, CONF_START_YEAR, DEFAULT_START_YEAR


class WPEnergyPredictorOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        registry = async_get(self.hass)
        candidates = []

        for ent in registry.entities.values():
            if ent.entity_id.startswith("sensor."):
                st = self.hass.states.get(ent.entity_id)
                if st:
                    try:
                        float(st.state)
                        candidates.append(ent.entity_id)
                    except:
                        pass

        schema = vol.Schema({
            vol.Required(CONF_SENSOR, default=self.config_entry.options.get(CONF_SENSOR, self.config_entry.data.get(CONF_SENSOR))): vol.In(sorted(candidates)),
            vol.Required(CONF_START_YEAR, default=self.config_entry.options.get(CONF_START_YEAR, DEFAULT_START_YEAR)): int
        })

        return self.async_show_form(step_id="init", data_schema=schema)