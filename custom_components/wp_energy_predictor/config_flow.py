from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN, CONF_SENSOR, CONF_PRICE_PER_KWH


def _get_energy_sensors(hass):
    """Filtert nur echte Energiesensoren heraus."""
    sensors = []

    for entity_id in hass.states.async_entity_ids("sensor"):
        state = hass.states.get(entity_id)
        if not state:
            continue

        attrs = state.attributes

        # --- Filterkriterien ---
        device_class = attrs.get("device_class")
        state_class = attrs.get("state_class")
        unit = attrs.get("unit_of_measurement")

        if device_class != "energy":
            continue

        if state_class not in ("total", "total_increasing"):
            continue

        if unit not in ("kWh", "Wh"):
            continue

        sensors.append(entity_id)

    return sensors


class WPEnergyPredictorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    @staticmethod
    def async_get_options_flow(config_entry):
        return WPEnergyPredictorOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="WP Energy Predictor",
                data=user_input
            )

        sensors = _get_energy_sensors(self.hass)

        if not sensors:
            return self.async_show_form(
                step_id="user",
                errors={"base": "no_energy_sensors_found"}
            )

        schema = vol.Schema({
            vol.Required(CONF_SENSOR): vol.In(sensors),
            vol.Optional(CONF_PRICE_PER_KWH, default=0.30): vol.Coerce(float),
        })

        return self.async_show_form(step_id="user", data_schema=schema)


class WPEnergyPredictorOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        sensors = _get_energy_sensors(self.hass)

        schema = vol.Schema({
            vol.Required(
                CONF_SENSOR,
                default=self.config_entry.options.get(
                    CONF_SENSOR, self.config_entry.data[CONF_SENSOR]
                )
            ): vol.In(sensors),
            vol.Optional(
                CONF_PRICE_PER_KWH,
                default=self.config_entry.options.get(
                    CONF_PRICE_PER_KWH, self.config_entry.data.get(CONF_PRICE_PER_KWH, 0.30)
                ),
            ): vol.Coerce(float),
        })

        return self.async_show_form(step_id="init", data_schema=schema)
