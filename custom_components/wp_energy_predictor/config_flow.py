from homeassistant import config_entries
import voluptuous as vol
from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
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


SECTION_CORRECTIONS = "month_corrections"


def _number_field():
    """A text-based numeric input.

    Deliberately NOT a number field / NumberSelector: the browser changes the
    value of `<input type="number">` on wheel and trackpad scroll while it has
    focus, which silently corrupts entries when scrolling through a long form.
    `tel` still brings up the numeric keypad on mobile but ignores scrolling.
    """
    return TextSelector(TextSelectorConfig(type=TextSelectorType.TEL))


def _format_number(value) -> str:
    """Render a stored number for a text field ('' when unset)."""
    if value is None or value == "":
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return str(int(number)) if number == int(number) else str(number)


def _parse_number(raw):
    """Parse user text into a float. Accepts '1234.5', '1234,5' and '1.234,5'.

    Returns None for an empty field. Raises ValueError on garbage.
    """
    if raw is None:
        return None
    text = str(raw).strip().replace(" ", "")
    if not text:
        return None
    if "," in text:                       # german decimal comma
        text = text.replace(".", "").replace(",", ".")
    return float(text)


def _corrections_section(existing: dict, key_map: dict[int, str], pending: dict | None = None):
    """A collapsible section holding the twelve monthly correction fields."""
    source = pending if pending is not None else existing
    fields = {}
    for _, key in key_map.items():
        fields[
            vol.Optional(key, description={"suggested_value": _format_number(source.get(key))})
        ] = _number_field()
    return section(vol.Schema(fields), {"collapsed": True})


def _collect(user_input: dict, key_map: dict[int, str]) -> tuple[dict, dict]:
    """Flatten the corrections section and coerce every text field to a number.

    Returns (values, errors). Keys left blank are omitted entirely, so clearing
    a field removes the correction — same behaviour as before the rewrite.
    """
    values = dict(user_input)
    corrections = values.pop(SECTION_CORRECTIONS, None) or {}
    errors: dict[str, str] = {}

    if CONF_PRICE_PER_KWH in values:
        try:
            price = _parse_number(values[CONF_PRICE_PER_KWH])
        except ValueError:
            errors["base"] = "invalid_number"
        else:
            if price is None:
                values.pop(CONF_PRICE_PER_KWH)
            else:
                values[CONF_PRICE_PER_KWH] = price

    for _, key in key_map.items():
        try:
            number = _parse_number(corrections.get(key))
        except ValueError:
            errors["base"] = "invalid_number"
            continue
        if number is not None:
            values[key] = number

    return values, errors


def _pending_corrections(user_input: dict | None, key_map: dict[int, str]) -> dict | None:
    """Keep what the user typed when the form is redisplayed after an error."""
    if not user_input:
        return None
    return dict(user_input.get(SECTION_CORRECTIONS) or {})


class WPEnergyPredictorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    @staticmethod
    def async_get_options_flow(config_entry):
        return WPEnergyPredictorOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            values, errors = _collect(user_input, {})
            if not errors:
                if values.get(CONF_WW_SENSOR) == CONF_NONE:
                    values.pop(CONF_WW_SENSOR, None)
                return self.async_create_entry(
                    title="WP Energy Predictor",
                    data=values
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
            vol.Optional(
                CONF_PRICE_PER_KWH,
                description={"suggested_value": "0.30"},
            ): _number_field(),
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

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class WPEnergyPredictorOptionsFlow(config_entries.OptionsFlow):
    """Options flow handler - config_entry is provided by parent class."""
    def __init__(self, config_entry):
        super().__init__()
        self._wp_config_entry = config_entry
        self._heat_data: dict = {}

    async def async_step_init(self, user_input=None):
        return await self.async_step_heat(user_input)

    async def async_step_heat(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            values, errors = _collect(user_input, HEAT_CORRECTION_KEYS)
            if not errors:
                self._heat_data = values
                return await self.async_step_warmwater()

        sensors = _get_energy_sensors(self.hass)
        options = self._wp_config_entry.options
        data = self._wp_config_entry.data

        price = options.get(CONF_PRICE_PER_KWH, data.get(CONF_PRICE_PER_KWH, 0.30))
        if user_input is not None:
            price = user_input.get(CONF_PRICE_PER_KWH, price)

        schema_dict = {
            vol.Required(
                CONF_SENSOR,
                default=options.get(CONF_SENSOR, data[CONF_SENSOR])
            ): vol.In(sensors),
            vol.Optional(
                CONF_PRICE_PER_KWH,
                description={"suggested_value": _format_number(price)},
            ): _number_field(),
            vol.Optional(
                CONF_LOAD_FACTOR_TYPE_HEAT,
                default=options.get(
                    CONF_LOAD_FACTOR_TYPE_HEAT,
                    data.get(CONF_LOAD_FACTOR_TYPE_HEAT, LOAD_FACTOR_PRESET_HEAT_STANDARD)
                )
            ): SelectSelector(
                SelectSelectorConfig(
                    options=_get_load_factor_options(),
                    mode=SelectSelectorMode.LIST,
                    translation_key="load_factor_preset",
                )
            ),
            vol.Required(SECTION_CORRECTIONS): _corrections_section(
                options, HEAT_CORRECTION_KEYS, _pending_corrections(user_input, HEAT_CORRECTION_KEYS)
            ),
        }

        return self.async_show_form(
            step_id="heat", data_schema=vol.Schema(schema_dict), errors=errors
        )

    async def async_step_warmwater(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            values, errors = _collect(user_input, WW_CORRECTION_KEYS)
            if not errors:
                if values.get(CONF_WW_SENSOR) == CONF_NONE:
                    values.pop(CONF_WW_SENSOR, None)
                return self.async_create_entry(title="", data={**self._heat_data, **values})

        sensors = _get_energy_sensors(self.hass)
        options = self._wp_config_entry.options
        data = self._wp_config_entry.data

        ww_default = options.get(CONF_WW_SENSOR, data.get(CONF_WW_SENSOR, CONF_NONE))
        if ww_default not in sensors:
            ww_default = CONF_NONE

        schema_dict = {
            vol.Optional(CONF_WW_SENSOR, default=ww_default): vol.In(_sensor_select_with_none(sensors)),
            vol.Optional(
                CONF_LOAD_FACTOR_TYPE_WW,
                default=options.get(
                    CONF_LOAD_FACTOR_TYPE_WW,
                    data.get(CONF_LOAD_FACTOR_TYPE_WW, LOAD_FACTOR_PRESET_WW_STANDARD)
                )
            ): SelectSelector(
                SelectSelectorConfig(
                    options=_get_load_factor_options(),
                    mode=SelectSelectorMode.LIST,
                    translation_key="load_factor_preset",
                )
            ),
            vol.Required(SECTION_CORRECTIONS): _corrections_section(
                options, WW_CORRECTION_KEYS, _pending_corrections(user_input, WW_CORRECTION_KEYS)
            ),
        }

        return self.async_show_form(
            step_id="warmwater", data_schema=vol.Schema(schema_dict), errors=errors
        )
