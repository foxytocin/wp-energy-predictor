from homeassistant import config_entries
import voluptuous as vol
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_LOAD_FACTOR_TYPE_HEAT,
    CONF_LOAD_FACTOR_TYPE_WW,
    CONF_NONE,
    CONF_PRICE_PER_KWH,
    CONF_SENSOR,
    CONF_WW_SENSOR,
    DOMAIN,
    LOAD_FACTOR_PRESET_HEAT_STANDARD,
    LOAD_FACTOR_PRESET_LINEAR,
    LOAD_FACTOR_PRESET_WW_STANDARD,
)


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


def _sensor_select_with_none(sensors: list[str]) -> dict[str, str]:
    return {CONF_NONE: "— nicht verwenden —", **{s: s for s in sensors}}


def _get_load_factor_options():
    return [
        LOAD_FACTOR_PRESET_HEAT_STANDARD,
        LOAD_FACTOR_PRESET_WW_STANDARD,
        LOAD_FACTOR_PRESET_LINEAR,
    ]


class WPEnergyPredictorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    @staticmethod
    def async_get_options_flow(config_entry):
        return WPEnergyPredictorOptionsFlow()

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            if user_input.get(CONF_WW_SENSOR) == CONF_NONE:
                user_input.pop(CONF_WW_SENSOR, None)
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
            vol.Optional(CONF_WW_SENSOR, default=CONF_NONE): vol.In(_sensor_select_with_none(sensors)),
            vol.Optional(CONF_PRICE_PER_KWH, default=0.30): vol.Coerce(float),
            vol.Optional(CONF_LOAD_FACTOR_TYPE_HEAT, default=LOAD_FACTOR_PRESET_HEAT_STANDARD): SelectSelector(
                SelectSelectorConfig(
                    options=_get_load_factor_options(),
                    mode=SelectSelectorMode.LIST,
                    translation_key="load_factor_preset",
                )
            ),
            vol.Optional(CONF_LOAD_FACTOR_TYPE_WW, default=LOAD_FACTOR_PRESET_WW_STANDARD): SelectSelector(
                SelectSelectorConfig(
                    options=_get_load_factor_options(),
                    mode=SelectSelectorMode.LIST,
                    translation_key="load_factor_preset",
                )
            ),
        })

        return self.async_show_form(step_id="user", data_schema=schema)


class WPEnergyPredictorOptionsFlow(config_entries.OptionsFlow):
    """Options flow handler - config_entry is provided by parent class."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            if user_input.get(CONF_WW_SENSOR) == CONF_NONE:
                user_input.pop(CONF_WW_SENSOR, None)
            return self.async_create_entry(title="", data=user_input)

        sensors = _get_energy_sensors(self.hass)

        ww_default = self.config_entry.options.get(
            CONF_WW_SENSOR, self.config_entry.data.get(CONF_WW_SENSOR, CONF_NONE)
        )
        if ww_default not in sensors:
            ww_default = CONF_NONE

        schema = vol.Schema({
            vol.Required(
                CONF_SENSOR,
                default=self.config_entry.options.get(
                    CONF_SENSOR, self.config_entry.data[CONF_SENSOR]
                )
            ): vol.In(sensors),
            vol.Optional(CONF_WW_SENSOR, default=ww_default): vol.In(_sensor_select_with_none(sensors)),
            vol.Optional(
                CONF_PRICE_PER_KWH,
                default=self.config_entry.options.get(
                    CONF_PRICE_PER_KWH, self.config_entry.data.get(CONF_PRICE_PER_KWH, 0.30)
                ),
            ): vol.Coerce(float),
            vol.Optional(
                CONF_LOAD_FACTOR_TYPE_HEAT,
                default=self.config_entry.options.get(
                    CONF_LOAD_FACTOR_TYPE_HEAT,
                    self.config_entry.data.get(CONF_LOAD_FACTOR_TYPE_HEAT, LOAD_FACTOR_PRESET_HEAT_STANDARD)
                )
            ): SelectSelector(
                SelectSelectorConfig(
                    options=_get_load_factor_options(),
                    mode=SelectSelectorMode.LIST,
                    translation_key="load_factor_preset",
                )
            ),
            vol.Optional(
                CONF_LOAD_FACTOR_TYPE_WW,
                default=self.config_entry.options.get(
                    CONF_LOAD_FACTOR_TYPE_WW,
                    self.config_entry.data.get(CONF_LOAD_FACTOR_TYPE_WW, LOAD_FACTOR_PRESET_WW_STANDARD)
                )
            ): SelectSelector(
                SelectSelectorConfig(
                    options=_get_load_factor_options(),
                    mode=SelectSelectorMode.LIST,
                    translation_key="load_factor_preset",
                )
            ),
        })

        return self.async_show_form(step_id="init", data_schema=schema)
