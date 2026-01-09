import logging
from datetime import datetime, timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.util.dt import now

UPDATE_INTERVAL = 300  # 5 minutes
_LOGGER = logging.getLogger(__name__)


def month_range(year, month):
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    return start, end


class WPDataCoordinator(DataUpdateCoordinator):
    """Coordinator calculating WP energy stats."""

    def __init__(self, hass, source_sensor):
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name="wp_energy_predictor",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.hass = hass
        self.source = source_sensor

    async def _async_update_data(self):
        """Fetch updated WP statistics."""
        year = now().year

        def get_change(start, end):
            stats = statistics_during_period(
                hass=self.hass,
                start_time=start,
                end_time=end,
                period="day",
                statistic_ids=[self.source],
                types=["change"],
                units=None,
            )
            if stats and self.source in stats:
                return float(stats[self.source][0]["change"])
            return 0.0

        results = {}

        # Historical months
        for month in range(1, 13):
            start, end = month_range(year, month)
            value = await self.hass.async_add_executor_job(get_change, start, end)
            results[f"month_{month}"] = value

        # Current month
        today = now()
        mstart, _ = month_range(today.year, today.month)
        real_current = await self.hass.async_add_executor_job(get_change, mstart, today)
        results["current_real"] = real_current

        # Daily average
        if today.day > 1:
            results["daily_avg"] = round(real_current / (today.day - 1), 3)
        else:
            results["daily_avg"] = 0.0

        return results