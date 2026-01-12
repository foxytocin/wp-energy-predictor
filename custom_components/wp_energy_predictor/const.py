DOMAIN = "wp_energy_predictor"
CONF_SENSOR = "sensor"
CONF_WW_SENSOR = "warmwater_sensor"
CONF_PRICE_PER_KWH = "price_per_kwh"
CONF_NONE = "__none__"

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
WARM_WATER_LOAD_FACTORS = {m: 1.0 for m in range(1, 13)}
