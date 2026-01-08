import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, CONF_SENSOR, CONF_START_YEAR, DEFAULT_START_YEAR

class WPEnergyPredictorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for WP Energy Predictor."""

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="WP Energy Predictor",
                data=user_input
            )

        registry = er.async_get(self.hass)

        # Only real sensor entities with numeric states
        candidates = []
        for entity in registry.entities.values():
            if entity.entity_id.startswith("sensor."):
                state = self.hass.states.get(entity.entity_id)
                if state and state.state not in ["unknown", "unavailable"]:
                    try:
                        float(state.state)
                        candidates.append(entity.entity_id)
                    except ValueError:
                        pass

        candidates = sorted(candidates)

        if not candidates:
            return self.async_abort(reason="no_sensors_found")

        schema = vol.Schema({
            vol.Required(CONF_SENSOR): vol.In(candidates),
            vol.Required(CONF_START_YEAR, default=DEFAULT_START_YEAR): int
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema
        )