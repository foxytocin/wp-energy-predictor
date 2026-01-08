from datetime import datetime, timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util.dt import now
from homeassistant.components.recorder.statistics import statistics_during_period

from .const import UPDATE_INTERVAL, HEAT_LOAD_FACTORS

LOGGER = logging.getLogger(__name__)

def month_range(dt):
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if dt.month == 12:
        end = dt.replace(year=dt.year + 1, month=1, day=1) - timedelta(seconds=1)
    else:
        end = dt.replace(month=dt.month + 1, day=1) - timedelta(seconds=1)
    return start, end


class WPDataCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, source):
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name="wp_energy_predictor",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.hass = hass
        self.source = source

    async def _async_update_data(self):
        dt = now()
        mstart, mend = month_range(dt)

        # statistics wrapper
        def get_stats(start, end):
            return statistics_during_period(
                self.hass, start, end,
                period="day",
                statistic_ids=[self.source],
                types=["change"],
                units=True
            )

        # current month real data
        real = await self.hass.async_add_executor_job(get_stats, mstart, dt)
        real_val = 0.0
        if real and self.source in real:
            real_val = float(real[self.source][0]["change"])

        day = dt.day
        avg = real_val / (day - 1) if day > 1 and real_val > 0 else 0.0

        _, me = month_range(dt)
        remaining_days = me.day - (day - 1)
        forecast_current = real_val + avg * remaining_days

        # monthly values
        months = {}
        for m in range(1, 13):
            if m < dt.month:
                # past
                pstart, pend = month_range(dt.replace(month=m, day=1))
                pst = await self.hass.async_add_executor_job(get_stats, pstart, pend)
                val = 0.0
                if pst and self.source in pst:
                    val = float(pst[self.source][0]["change"])
                months[m] = val

            elif m == dt.month:
                # current
                months[m] = forecast_current

            else:
                # future
                fc_now = HEAT_LOAD_FACTORS[dt.month]
                fc_t = HEAT_LOAD_FACTORS[m]
                if fc_now > 0:
                    months[m] = real_val * fc_t / fc_now
                else:
                    months[m] = 0.0

        year_total = sum(months.values())

        return {
            "real": real_val,
            "avg": avg,
            "forecast_current": forecast_current,
            "months": months,
            "year": year_total,
        }