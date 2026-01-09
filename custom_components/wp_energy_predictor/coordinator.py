import logging
from datetime import datetime, timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.util.dt import now

_LOGGER = logging.getLogger(__name__)
UPDATE_INTERVAL = 300   # 5 minutes


def month_range(year, month):
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    return start, end


class WPDataCoordinator(DataUpdateCoordinator):
    """Coordinator calculating monthly statistics for heat pump."""

    def __init__(self, hass, source):
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name="wp_energy_predictor",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.hass = hass
        self.source = source

    async def _async_update_data(self):
        """Load all month statistics + forecast."""
        year = now().year
        today = now()

        def read_stats(start, end):
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

        months = {}

        # Read all 12 months
        for m in range(1, 12 + 1):
            mstart, mend = month_range(year, m)
            value = await self.hass.async_add_executor_job(read_stats, mstart, mend)
            months[m] = value

        # Current month real energy so far
        mstart, _ = month_range(today.year, today.month)
        current_real = await self.hass.async_add_executor_job(read_stats, mstart, today)

        # Daily average
        if today.day > 1:
            daily_avg = round(current_real / (today.day - 1), 3)
        else:
            daily_avg = 0.0

        return {
            "months": months,
            "current_real": current_real,
            "daily_avg": daily_avg,
        }