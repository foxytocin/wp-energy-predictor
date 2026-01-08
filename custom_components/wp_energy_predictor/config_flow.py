
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.entity_registry import async_get
from .const import DOMAIN, CONF_SENSOR
from .options_flow import WPEnergyPredictorOptionsFlow

class WPEnergyPredictorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, user_input=None):
        if user_input:
            return self.async_create_entry(title="WP Energy Predictor", data=user_input)

        reg = async_get(self.hass)
        sensors=[e.entity_id for e in reg.entities.values() if e.entity_id.startswith("sensor.")]
        schema=vol.Schema({vol.Required(CONF_SENSOR): vol.In(sorted(sensors))})
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    def async_get_options_flow(config_entry):
        return WPEnergyPredictorOptionsFlow(config_entry)
