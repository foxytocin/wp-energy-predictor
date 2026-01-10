from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_SENSOR
from .coordinator import WPEnergyPredictorCoordinator


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    sensor_id = entry.data[CONF_SENSOR]
    coordinator = WPEnergyPredictorCoordinator(hass, sensor_id)
    await coordinator.async_config_entry_first_refresh()

    entities = [
        CurrentMonthRealSensor(coordinator),
        DailyAverageSensor(coordinator),
        CurrentMonthForecastSensor(coordinator),
        YearForecastSensor(coordinator),
    ]

    for m in range(1, 13):
        entities.append(MonthSensor(coordinator, m))

    async_add_entities(entities)


class BaseSensor(SensorEntity):
    _attr_native_unit_of_measurement = "kWh"

    def __init__(self, coordinator):
        self.coordinator = coordinator

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self.coordinator.last_update_success

    async def async_update(self):
        await self.coordinator.async_request_refresh()


class CurrentMonthRealSensor(BaseSensor):
    _attr_name = "FMS WP Current Month Real"
    _attr_unique_id = "fms_wp_current_month_real"

    @property
    def native_value(self):
        return round(self.coordinator.data["current_real"], 2)


class DailyAverageSensor(BaseSensor):
    _attr_name = "FMS WP Daily Average"
    _attr_unique_id = "fms_wp_daily_average"

    @property
    def native_value(self):
        return round(self.coordinator.data["daily_avg"], 3)


class CurrentMonthForecastSensor(BaseSensor):
    _attr_name = "FMS WP Current Month Forecast"
    _attr_unique_id = "fms_wp_current_month_forecast"

    @property
    def native_value(self):
        return round(self.coordinator.data["forecast_current"], 2)


class YearForecastSensor(BaseSensor):
    _attr_name = "FMS WP Year Forecast"
    _attr_unique_id = "fms_wp_year_forecast"

    @property
    def native_value(self):
        return round(self.coordinator.data["year_forecast"], 2)


class MonthSensor(BaseSensor):
    def __init__(self, coordinator, month):
        super().__init__(coordinator)
        self.month = month
        self._attr_name = f"FMS WP Month {month}"
        self._attr_unique_id = f"fms_wp_month_{month}"

    @property
    def native_value(self):
        return round(self.coordinator.data["months"][self.month], 2)