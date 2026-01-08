from datetime import datetime
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.util.dt import now, start_of_month, end_of_month

from .const import HEAT_LOAD_FACTORS, CONF_SENSOR, DOMAIN


def get_month_stats(hass, entity_id, year, month):
    start = datetime(year, month, 1)
    end = end_of_month(start)

    stats = statistics_during_period(
        hass,
        start,
        end,
        [entity_id],
        "change"
    )

    if stats and entity_id in stats:
        return float(stats[entity_id][0]["change"])
    return 0.0


async def async_setup_entry(hass, entry, async_add_entities):
    source = entry.data[CONF_SENSOR]

    entities = [
        DailyAverageSensor(hass, source),
        CurrentRealMonthSensor(hass, source),
        CurrentMonthForecastSensor(hass, source),
        YearForecastSensor(hass)
    ]

    for m in range(1, 13):
        entities.append(MonthSensor(hass, source, m))

    async_add_entities(entities)


class DailyAverageSensor(SensorEntity):
    _attr_name = "WP Daily Average"
    _attr_unique_id = "wp_daily_average"
    _attr_native_unit_of_measurement = "kWh"

    def __init__(self, hass, source):
        self.hass = hass
        self.source = source

    @property
    def native_value(self):
        today = now()
        stats = statistics_during_period(
            self.hass,
            start_of_month(today),
            today,
            [self.source],
            "change"
        )
        if not stats or self.source not in stats:
            return 0.0

        real = float(stats[self.source][0]["change"])
        day = today.day

        if day <= 1:
            return 0.0

        return round(real / (day - 1), 2)


class CurrentRealMonthSensor(SensorEntity):
    _attr_name = "WP Current Month Real"
    _attr_unique_id = "wp_current_real"
    _attr_native_unit_of_measurement = "kWh"

    def __init__(self, hass, source):
        self.hass = hass
        self.source = source

    @property
    def native_value(self):
        today = now()
        stats = statistics_during_period(
            self.hass,
            start_of_month(today),
            today,
            [self.source],
            "change"
        )
        if stats and self.source in stats:
            return float(stats[self.source][0]["change"])
        return 0.0


class CurrentMonthForecastSensor(SensorEntity):
    _attr_name = "WP Current Month Forecast"
    _attr_unique_id = "wp_current_forecast"
    _attr_native_unit_of_measurement = "kWh"

    def __init__(self, hass, source):
        self.hass = hass
        self.source = source

    @property
    def native_value(self):
        today = now()

        real = float(self.hass.states.get("sensor.wp_current_real").state)
        avg = float(self.hass.states.get("sensor.wp_daily_average").state)

        total_days = end_of_month(today).day
        remaining = total_days - (today.day - 1)

        return round(real + avg * remaining, 2)


class MonthSensor(SensorEntity):
    _attr_native_unit_of_measurement = "kWh"

    def __init__(self, hass, source, month):
        self.hass = hass
        self.source = source
        self.month = month
        self._attr_name = f"WP Month {month}"
        self._attr_unique_id = f"wp_month_{month}"

    @property
    def native_value(self):
        today = now()
        current_month = today.month

        real_current = float(self.hass.states["sensor.wp_current_real"].state)
        forecast_current = float(self.hass.states["sensor.wp_current_forecast"].state)

        # Vergangener Monat
        if self.month < current_month:
            return get_month_stats(self.hass, self.source, today.year, self.month)

        # Aktueller Monat
        if self.month == current_month:
            return forecast_current

        # Zukunftsmonat
        fc_now = HEAT_LOAD_FACTORS[current_month]
        fc_target = HEAT_LOAD_FACTORS[self.month]

        if fc_now == 0:
            return 0.0

        return round(real_current * fc_target / fc_now, 2)


class YearForecastSensor(SensorEntity):
    _attr_name = "WP Year Forecast"
    _attr_unique_id = "wp_year_forecast"
    _attr_native_unit_of_measurement = "kWh"

    @property
    def native_value(self):
        total = 0.0
        for m in range(1, 13):
            ent = self.hass.states.get(f"sensor.wp_month_{m}")
            if ent:
                total += float(ent.state)
        return round(total, 2)