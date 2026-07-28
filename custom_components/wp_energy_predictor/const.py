DOMAIN = "wp_energy_predictor"
CONF_SENSOR = "sensor"
CONF_WW_SENSOR = "warmwater_sensor"
CONF_PRICE_PER_KWH = "price_per_kwh"
CONF_NONE = "__none__"

MONTHS = tuple(range(1, 13))

# Derived from measured data instead of a generic heat-pump curve.
# Model: kWh = -65.2 + 11.54 * (HDD / COP), R2 = 0.974
#   HDD = heating degree days, base 20 C / heating limit 15 C, from daily
#         outdoor temperatures (Jan-Jul 2026, Aug-Dec 2025)
#   COP = 3.29 + 0.073 * T_outdoor, fitted on the measured monthly COP
#         (3.16 at 1.5 C ... 4.22 at 14.9 C)
# Degree days alone are not enough for a heat pump: they model heat demand,
# while the electricity drawn is heat/COP -- and the COP itself rises with
# outdoor temperature. Both effects compound, which is why the previous
# generic curve was too flat in the shoulder months and too high in December.
HEAT_LOAD_FACTORS = {
    1: 1.00,
    2: 0.65,
    3: 0.60,
    4: 0.36,
    5: 0.14,
    6: 0.01,
    7: 0.01,
    8: 0.01,
    9: 0.09,
    10: 0.38,
    11: 0.58,
    12: 0.69
}

# Warm water typically has much less seasonality than space heating. Keep it flat by default.
#WARM_WATER_LOAD_FACTORS = {m: 1.0 for m in range(1, 13)}
WARM_WATER_LOAD_FACTORS = {
    1: 1.15,  # Januar (kältestes Wasser, hohe Verluste)
    2: 1.12,
    3: 1.05,
    4: 0.98,
    5: 0.92,
    6: 0.87,
    7: 0.85,  # Juli (Minimum)
    8: 0.86,
    9: 0.92,
    10: 1.00,
    11: 1.07,
    12: 1.14,
}

LINEAR_FACTORS = {m: 1.0 for m in range(1, 13)}

HEAT_CORRECTION_KEYS = {m: f"heat_correction_{m}" for m in MONTHS}
WW_CORRECTION_KEYS = {m: f"ww_correction_{m}" for m in MONTHS}

# Configuration Constants
CONF_LOAD_FACTOR_TYPE_HEAT = "load_factor_type_heat"
CONF_LOAD_FACTOR_TYPE_WW = "load_factor_type_ww"

# Presets
LOAD_FACTOR_PRESET_HEAT_STANDARD = "heat_pump_standard"
LOAD_FACTOR_PRESET_WW_STANDARD = "warm_water_standard"
LOAD_FACTOR_PRESET_LINEAR = "linear"
