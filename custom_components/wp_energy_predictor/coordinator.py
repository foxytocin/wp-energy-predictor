from datetime import datetime, timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import statistics_during_period

from .const import UPDATE_INTERVAL


_LOGGER = logging.getLogger(__name__)


class WPDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, source: str):
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name="wp_energy_predictor",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.source = source

    async def _async_update_data(self):
        """Fetch data from recorder safely using the DB executor."""
        now = datetime.now()

        # Start / end of current month
        mstart = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # --------- DB-CALL inside executor only ----------
        def get_stats(start, end):
            return statistics_during_period(
                hass=self.hass,
                start_time=start,
                end_time=end,
                period="hour",
                statistic_ids=[self.source],
                types=["change"],
                units=None,
            )

        real_stats = await get_instance(self.hass).async_add_executor_job(
            get_stats, mstart, now
        )
        # --------------------------------------------------

        # Extract real usage
        if (
            real_stats
            and self.source in real_stats
            and len(real_stats[self.source]) > 0
        ):
            current_real = float(real_stats[self.source][0]["change"])
        else:
            current_real = 0.0

        # Daily average
        if now.day > 1:
            daily_avg = round(current_real / (now.day - 1), 3)
        else:
            daily_avg = 0.0

        # Build 12 months array (only current month initially real)
        months = {}
        for month in range(1, 13):
            if month == now.month:
                months[month] = current_real
            else:
                months[month] = 0.0  # future months will be filled by sensors

        return {
            "current_real": current_real,
            "daily_avg": daily_avg,
            "months": months,
        }