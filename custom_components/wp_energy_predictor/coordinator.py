import logging
from datetime import datetime, timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.util.dt import now

UPDATE_INTERVAL = 300  # 5 minutes
_LOGGER = logging.getLogger(__name__)


def month_range(year, month):
    """Return (start, end) datetimes for one month."""
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    return start, end


class WPDataCoordinator(DataUpdateCoordinator):
    """Coordinator that calculates monthly statistics for the heat pump."""

    def __init__(self, hass, source_sensor):
        super().__init__(
            hass,
            _LOGGER,
            "wp_energy_predictor",
            timedelta(seconds=UPDATE_INTERVAL),
        )
        self.hass = hass
        self.source = source_sensor

    async def _async_update_data(self):
        """Retrieve real consumption values from recorder statistics."""

        year = now().year

        # Function executed in executor to avoid blocking DB calls
        def get_change(start, end):
            """Return total consumption change between start and end."""
            stats = statistics_during_period(
                self.hass,
                start,
                end,
                "day",               # HA expects: "5minute", "hour", "day"
                [self.source],
                ["change"],
                None,
            )
            if stats and self.source in stats:
                return float(stats[self.source][0]["change"])
            return 0.0

        results = {}

        # Fill historical months (Jan … Dec)
        for month in range(1, 13):
            start, end = month_range(year, month)
            value = await self.hass.async_add_executor_job(get_change, start, end)
            results[f"month_{month}"] = value

        # ------------------------------------
        # Current month real consumption
        # ------------------------------------
        today = now()
        mstart, _ = month_range(today.year, today.month)

        real_current = await self.hass.async_add_executor_job(
            get_change, mstart, today
        )
        results["current_real"] = real_current

        # ------------------------------------
        # Daily average
        # ------------------------------------
        if today.day > 1:
            results["daily_avg"] = round(real_current / (today.day - 1), 3)
        else:
            results["daily_avg"] = 0.0

        return results