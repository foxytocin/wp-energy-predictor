import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import entity_registry as er
from .const import DOMAIN, CONF_SENSOR, CONF_START_YEAR, DEFAULT_START_YEAR

class WPEnergyPredictorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input:
            return self.async_create_entry(title="WP Energy Predictor", data=user_input)
        registry=er.async_get(self.hass)
        candidates=sorted([e.entity_id for e in registry.entities.values() if e.entity_id.startswith("sensor.")])
        schema=vol.Schema({
            vol.Required(CONF_SENSOR): vol.In(candidates),
            vol.Required(CONF_START_YEAR, default=DEFAULT_START_YEAR): int
        })
        return self.async_show_form(step_id="user", data_schema=schema)
