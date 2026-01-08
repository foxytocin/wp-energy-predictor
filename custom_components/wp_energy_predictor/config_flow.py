
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.entity_registry import async_get

from .const import DOMAIN, CONF_SENSOR, CONF_START_YEAR, DEFAULT_START_YEAR
from .options_flow import WPEnergyPredictorOptionsFlow

class WPEnergyPredictorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input:
            return self.async_create_entry(title="WP Energy Predictor", data=user_input)

        registry = async_get(self.hass)
        sensors=[]
        for ent in registry.entities.values():
            if ent.entity_id.startswith("sensor."):
                st=self.hass.states.get(ent.entity_id)
                if st:
                    try:
                        float(st.state)
                        sensors.append(ent.entity_id)
                    except:
                        pass

        if not sensors:
            return self.async_abort(reason="no_valid_sensors")

        schema = vol.Schema({
            vol.Required(CONF_SENSOR): vol.In(sorted(sensors)),
            vol.Required(CONF_START_YEAR, default=DEFAULT_START_YEAR): int
        })

        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    def async_get_options_flow(entry):
        return WPEnergyPredictorOptionsFlow(entry)
