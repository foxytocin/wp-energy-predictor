import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.entity_registry import async_get
from .const import DOMAIN, CONF_SENSOR, CONF_START_YEAR, DEFAULT_START_YEAR


class WPEnergyPredictorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for WP Energy Predictor."""

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="WP Energy Predictor",
                data=user_input
            )

        registry = async_get(self.hass)

        candidates = []
        for entity in registry.entities.values():
            if entity.entity_id.startswith("sensor."):
                state = self.hass.states.get(entity.entity_id)
                if state:
                    try:
                        float(state.state)
                        candidates.append(entity.entity_id)
                    except:
                        pass

        if not candidates:
            return self.async_abort(reason="no_sensors_found")

        schema = vol.Schema({
            vol.Required(CONF_SENSOR): vol.In(sorted(candidates)),
            vol.Required(CONF_START_YEAR, default=DEFAULT_START_YEAR): int,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
        )