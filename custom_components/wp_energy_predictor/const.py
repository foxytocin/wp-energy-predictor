DOMAIN = "wp_energy_predictor"
CONF_SENSOR = "sensor"
CONF_WW_SENSOR = "warmwater_sensor"
CONF_PRICE_PER_KWH = "price_per_kwh"
CONF_NONE = "__none__"

MONTHS = tuple(range(1, 13))

HEAT_LOAD_FACTORS = {
    1: 1.30,
    2: 1.15,
    3: 1.05,
    4: 0.85,
    5: 0.60,
    6: 0.40,
    7: 0.35,
    8: 0.40,
    9: 0.55,
    10: 0.75,
    11: 1.00,
    12: 1.20,
}

# Warm water typically has much less seasonality than space heating. Keep it flat by default.
#WARM_WATER_LOAD_FACTORS = {m: 1.0 for m in range(1, 13)}
WARM_WATER_LOAD_FACTORS = {
    1: 1.20,  # Januar (kältestes Wasser, hohe Verluste)
    2: 1.15,
    3: 1.05,
    4: 0.95,
    5: 0.85,
    6: 0.75,
    7: 0.70,  # Juli (Minimum)
    8: 0.80,
    9: 0.95,
    10: 1.05,
    11: 1.10,
    12: 1.15,
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
