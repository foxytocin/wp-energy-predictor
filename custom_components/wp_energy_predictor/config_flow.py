from homeassistant import config_entries
import voluptuous as vol
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    HEAT_CORRECTION_KEYS,
    WW_CORRECTION_KEYS,
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


def _add_month_corrections(schema_dict, existing: dict, key_map: dict[int, str]):
    """Add optional month correction fields to a voluptuous schema dict."""
    for _, key in key_map.items():
        existing_value = existing.get(key)
        if existing_value is not None:
            schema_dict[vol.Optional(key, default=existing_value)] = vol.Coerce(float)
        else:
            schema_dict[vol.Optional(key)] = vol.Coerce(float)


class WPEnergyPredictorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    @staticmethod
    def async_get_options_flow(config_entry):
        return WPEnergyPredictorOptionsFlow(config_entry)

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
    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.hass = config_entry.hass
        self._heat_data: dict = {}

    async def async_step_init(self, user_input=None):
        return await self.async_step_heat(user_input)

    async def async_step_heat(self, user_input=None):
        if user_input is not None:
            self._heat_data = user_input
            return await self.async_step_warmwater()

        sensors = _get_energy_sensors(self.hass)

        schema_dict = {
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
        }

        _add_month_corrections(schema_dict, self.config_entry.options, HEAT_CORRECTION_KEYS)

        schema = vol.Schema(schema_dict)

        return self.async_show_form(step_id="heat", data_schema=schema)

    async def async_step_warmwater(self, user_input=None):
        if user_input is not None:
            if user_input.get(CONF_WW_SENSOR) == CONF_NONE:
                user_input.pop(CONF_WW_SENSOR, None)
            data = {**self._heat_data, **user_input}
            return self.async_create_entry(title="", data=data)

        sensors = _get_energy_sensors(self.hass)

        ww_default = self.config_entry.options.get(
            CONF_WW_SENSOR, self.config_entry.data.get(CONF_WW_SENSOR, CONF_NONE)
        )
        if ww_default not in sensors:
            ww_default = CONF_NONE

        schema_dict = {
            vol.Optional(CONF_WW_SENSOR, default=ww_default): vol.In(_sensor_select_with_none(sensors)),
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
        }

        _add_month_corrections(schema_dict, self.config_entry.options, WW_CORRECTION_KEYS)

        schema = vol.Schema(schema_dict)

        return self.async_show_form(step_id="warmwater", data_schema=schema)
