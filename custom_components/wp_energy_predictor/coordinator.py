from datetime import datetime, timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.components.recorder import get_instance

UPDATE_INTERVAL = 300  # 5 Minuten


def month_range(dt):
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if dt.month == 12:
        end = dt.replace(year=dt.year + 1, month=1, day=1)
    else:
        end = dt.replace(month=dt.month + 1, day=1)
    return start, end


class WPDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, source_entity):
        self.hass = hass
        self.source = source_entity

        super().__init__(
            hass,
            logging.getLogger(__name__),
            name="wp_energy_predictor",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self):
        """Fetch statistics for all months + daily average."""

        now = datetime.now()
        rec = get_instance(self.hass)

        def get_stats(start, end):
            """Runs inside executor → safe for DB access."""

            stats = statistics_during_period(
                hass=self.hass,
                start_time=start,
                end_time=end,
                statistic_ids=[self.source],
                period="day",
                types=["change"],
                units={},  # MUST be dict, NOT bool!
            )

            if stats and self.source in stats:
                try:
                    return float(stats[self.source][0]["change"])
                except Exception:
                    return 0.0

            return 0.0

        # Monatliche Werte
        months = {}
        for m in range(1, 13):
            mstart = now.replace(month=m, day=1, hour=0, minute=0, second=0, microsecond=0)

            # Monatsende bestimmen
            if m == 12:
                mend = now.replace(year=now.year + 1, month=1, day=1)
            else:
                mend = now.replace(month=m + 1, day=1)

            # Heute nur bis jetzt berechnen
            if m == now.month:
                mend = now

            real_value = await self.hass.async_add_executor_job(get_stats, mstart, mend)
            months[m] = real_value

        # Current real
        current_real = months[now.month]

        # Daily average korrekt berechnen
        if now.day > 1:
            daily_avg = round(current_real / (now.day - 1), 3)
        else:
            daily_avg = 0.0

        return {
            "months": months,
            "current_real": current_real,
            "daily_avg": daily_avg,
        }