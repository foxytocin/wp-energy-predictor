from datetime import datetime, timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.components.recorder import get_instance as recorder_get
from homeassistant.util.dt import now

UPDATE_INTERVAL = 300  # 5 min


def month_range(year, month):
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    return start, end


class WPDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, source_sensor):
        super().__init__(
            hass,
            name="wp_energy_predictor",
            update_interval=timedelta(seconds=UPDATE_INTERVAL)
        )
        self.hass = hass
        self.source = source_sensor

    async def _async_update_data(self):
        year = now().year

        def get_change(start, end):
            """Runs inside executor → must NOT block event loop"""
            stats = statistics_during_period(
                self.hass,
                start,
                end,
                "day",
                [self.source],
                ["change"],
                None
            )
            if stats and self.source in stats:
                return float(stats[self.source][0]["change"])
            return 0.0

        results = {}

        # monthly real values (including historical months)
        for month in range(1, 13):
            start, end = month_range(year, month)
            value = await self.hass.async_add_executor_job(get_change, start, end)
            results[f"month_{month}"] = value

        # current month real
        today = now()
        mstart, mend = month_range(today.year, today.month)
        real_current = await self.hass.async_add_executor_job(get_change, mstart, today)
        results["current_real"] = real_current

        # daily avg
        if today.day > 1:
            results["daily_avg"] = round(real_current / (today.day - 1), 3)
        else:
            results["daily_avg"] = 0.0

        return results