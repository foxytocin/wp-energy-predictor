from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WPEnergyPredictorCoordinator


@dataclass(frozen=True, kw_only=True)
class WPEnergyPredictorSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[dict], float]


SENSOR_DESCRIPTIONS: tuple[WPEnergyPredictorSensorEntityDescription, ...] = (
    WPEnergyPredictorSensorEntityDescription(
        key="current_month_real",
        name="FMS WP Current Month Real",
        value_fn=lambda data: float(data["current_real"]),
    ),
    WPEnergyPredictorSensorEntityDescription(
        key="daily_average",
        name="FMS WP Daily Average",
        value_fn=lambda data: float(data["daily_avg"]),
    ),
    WPEnergyPredictorSensorEntityDescription(
        key="current_month_forecast",
        name="FMS WP Current Month Forecast",
        value_fn=lambda data: float(data["forecast_current"]),
    ),
    WPEnergyPredictorSensorEntityDescription(
        key="year_forecast",
        name="FMS WP Year Forecast",
        value_fn=lambda data: float(data["year_forecast"]),
    ),
)

WW_SENSOR_DESCRIPTIONS: tuple[WPEnergyPredictorSensorEntityDescription, ...] = (
    WPEnergyPredictorSensorEntityDescription(
        key="current_month_real",
        name="FMS WW Current Month Real",
        value_fn=lambda data: float(data["current_real"]),
    ),
    WPEnergyPredictorSensorEntityDescription(
        key="daily_average",
        name="FMS WW Daily Average",
        value_fn=lambda data: float(data["daily_avg"]),
    ),
    WPEnergyPredictorSensorEntityDescription(
        key="current_month_forecast",
        name="FMS WW Current Month Forecast",
        value_fn=lambda data: float(data["forecast_current"]),
    ),
    WPEnergyPredictorSensorEntityDescription(
        key="year_forecast",
        name="FMS WW Year Forecast",
        value_fn=lambda data: float(data["year_forecast"]),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator_data = hass.data[DOMAIN][entry.entry_id]
    if isinstance(coordinator_data, dict):
        heat_coordinator: WPEnergyPredictorCoordinator = coordinator_data["heat"]
        ww_coordinator: WPEnergyPredictorCoordinator | None = coordinator_data.get("ww")
    else:
        heat_coordinator = coordinator_data
        ww_coordinator = None

    entities: list[SensorEntity] = [
        WPEnergyPredictorSensor(heat_coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    ]
    entities.extend(MonthSensor(heat_coordinator, entry, m) for m in range(1, 13))
    entities.extend(MonthCostSensor(heat_coordinator, entry, m) for m in range(1, 13))
    entities.append(YearCostForecastSensor(heat_coordinator, entry))

    if ww_coordinator is not None:
        entities.extend(
            WWEnergyPredictorSensor(ww_coordinator, entry, description)
            for description in WW_SENSOR_DESCRIPTIONS
        )
        entities.extend(WWMonthSensor(ww_coordinator, entry, m) for m in range(1, 13))
        entities.extend(WWMonthCostSensor(ww_coordinator, entry, m) for m in range(1, 13))
        entities.append(WWYearCostForecastSensor(ww_coordinator, entry))

    async_add_entities(entities)


class WPEnergyPredictorSensor(CoordinatorEntity[WPEnergyPredictorCoordinator], SensorEntity):
    _attr_native_unit_of_measurement = "kWh"

    def __init__(
        self,
        coordinator: WPEnergyPredictorCoordinator,
        entry: ConfigEntry,
        description: WPEnergyPredictorSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "WP Energy Predictor",
        }

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        try:
            return round(self.entity_description.value_fn(self.coordinator.data), 2)
        except (KeyError, TypeError):
            return None


class WWEnergyPredictorSensor(CoordinatorEntity[WPEnergyPredictorCoordinator], SensorEntity):
    _attr_native_unit_of_measurement = "kWh"

    def __init__(
        self,
        coordinator: WPEnergyPredictorCoordinator,
        entry: ConfigEntry,
        description: WPEnergyPredictorSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry.entry_id}_ww_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "WP Energy Predictor",
        }

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        try:
            return round(self.entity_description.value_fn(self.coordinator.data), 2)
        except (KeyError, TypeError):
            return None


class MonthSensor(CoordinatorEntity[WPEnergyPredictorCoordinator], SensorEntity):
    _attr_native_unit_of_measurement = "kWh"

    def __init__(
        self,
        coordinator: WPEnergyPredictorCoordinator,
        entry: ConfigEntry,
        month: int,
    ) -> None:
        super().__init__(coordinator)
        self._month = month
        self._attr_name = f"FMS WP Month {month}"
        self._attr_unique_id = f"{entry.entry_id}_month_{month}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "WP Energy Predictor",
        }

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("months", {}).get(self._month)


class WWMonthSensor(CoordinatorEntity[WPEnergyPredictorCoordinator], SensorEntity):
    _attr_native_unit_of_measurement = "kWh"

    def __init__(
        self,
        coordinator: WPEnergyPredictorCoordinator,
        entry: ConfigEntry,
        month: int,
    ) -> None:
        super().__init__(coordinator)
        self._month = month
        self._attr_name = f"FMS WW Month {month}"
        self._attr_unique_id = f"{entry.entry_id}_ww_month_{month}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "WP Energy Predictor",
        }

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("months", {}).get(self._month)


class MonthCostSensor(CoordinatorEntity[WPEnergyPredictorCoordinator], SensorEntity):
    def __init__(
        self,
        coordinator: WPEnergyPredictorCoordinator,
        entry: ConfigEntry,
        month: int,
    ) -> None:
        super().__init__(coordinator)
        self._month = month
        self._attr_name = f"FMS WP Month {month} Cost"
        self._attr_unique_id = f"{entry.entry_id}_month_{month}_cost"
        self._attr_native_unit_of_measurement = coordinator.hass.config.currency
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "WP Energy Predictor",
        }

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("month_costs", {}).get(self._month)


class WWMonthCostSensor(CoordinatorEntity[WPEnergyPredictorCoordinator], SensorEntity):
    def __init__(
        self,
        coordinator: WPEnergyPredictorCoordinator,
        entry: ConfigEntry,
        month: int,
    ) -> None:
        super().__init__(coordinator)
        self._month = month
        self._attr_name = f"FMS WW Month {month} Cost"
        self._attr_unique_id = f"{entry.entry_id}_ww_month_{month}_cost"
        self._attr_native_unit_of_measurement = coordinator.hass.config.currency
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "WP Energy Predictor",
        }

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("month_costs", {}).get(self._month)


class YearCostForecastSensor(CoordinatorEntity[WPEnergyPredictorCoordinator], SensorEntity):
    def __init__(
        self,
        coordinator: WPEnergyPredictorCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_name = "FMS WP Year Cost Forecast"
        self._attr_unique_id = f"{entry.entry_id}_year_cost_forecast"
        self._attr_native_unit_of_measurement = coordinator.hass.config.currency
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "WP Energy Predictor",
        }

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("year_cost_forecast")


class WWYearCostForecastSensor(CoordinatorEntity[WPEnergyPredictorCoordinator], SensorEntity):
    def __init__(
        self,
        coordinator: WPEnergyPredictorCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_name = "FMS WW Year Cost Forecast"
        self._attr_unique_id = f"{entry.entry_id}_ww_year_cost_forecast"
        self._attr_native_unit_of_measurement = coordinator.hass.config.currency
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "WP Energy Predictor",
        }

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("year_cost_forecast")
