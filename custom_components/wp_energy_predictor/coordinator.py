from datetime import datetime, timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import statistics_during_period


UPDATE_INTERVAL = 300  # 5 Minuten


def month_start_end(dt):
    """Return start and end for a month."""
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if dt.month == 12:
        end = dt.replace(year=dt.year + 1, month=1, day=1)
    else:
        end = dt.replace(month=dt.month + 1, day=1)

    return start, end


def collect_all_stats(hass, source):
    """
    THIS RUNS IN THE EXECUTOR THREAD.
    Home Assistant will NOT warn about DB access here.
    """

    now = datetime.now()

    def get_stats(start, end):
        """Safe wrapper for statistics_during_period inside executor."""
        stats = statistics_during_period(
            hass=hass,
            start_time=start,
            end_time=end,
            statistic_ids=[source],
            period="day",
            types=["change"],
            units={},  # dict, not bool
        )

        if stats and source in stats:
            try:
                return float(stats[source][0]["change"])
            except Exception:
                return 0.0
        return 0.0

    # MONTHS
    months = {}
    for m in range(1, 13):
        mstart = now.replace(month=m, day=1, hour=0, minute=0, second=0, microsecond=0)

        # Month end
        if m == 12:
            mend = now.replace(year=now.year + 1, month=1, day=1)
        else:
            mend = now.replace(month=m + 1, day=1)

        # Current month → only until now
        if m == now.month:
            mend = now

        months[m] = get_stats(mstart, mend)

    current_real = months[now.month]

    # DAILY AVERAGE
    if now.day > 1:
        daily_avg = round(current_real / (now.day - 1), 3)
    else:
        daily_avg = 0.0

    return {
        "months": months,
        "current_real": current_real,
        "daily_avg": daily_avg,
    }


class WPDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, source_entity):
        self.source = source_entity

        super().__init__(
            hass,
            logging.getLogger(__name__),
            name="wp_energy_predictor",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self):
        """
        ABSOLUTELY NO DB CALLS HERE!
        Only call the executor job.
        """
        rec = get_instance(self.hass)  # required, but not directly used

        return await self.hass.async_add_executor_job(
            collect_all_stats, self.hass, self.source
        )