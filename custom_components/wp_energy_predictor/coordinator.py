from datetime import datetime, timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util.dt import now
from homeassistant.components.recorder.statistics import statistics_during_period

from .const import UPDATE_INTERVAL, HEAT_LOAD_FACTORS

LOGGER = logging.getLogger(__name__)


def month_range(dt: datetime):
    """Return first and last second of month."""
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if dt.month == 12:
        end = dt.replace(year=dt.year + 1, month=1, day=1) - timedelta(seconds=1)
    else:
        end = dt.replace(month=dt.month + 1, day=1) - timedelta(seconds=1)
    return start, end


class WPDataCoordinator(DataUpdateCoordinator):
    """Coordinator für WP Energy Predictor"""

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
        """Berechnet alle Real-, Forecast- und Monatswerte."""

        dt = now()

        #
        # ---- REALER VERBRAUCH DES AKTUELLEN MONATS ----
        #
        month_start, _ = month_range(dt)

        # Wichtig: end_time = jetzt, NICHT Monatsende
        def get_stats(start, end):
            stats = statistics_during_period(
                hass=self.hass,
                start_time=start,
                end_time=end,
                statistic_ids=[self.source],
                types=["change"],
                units=None,
            )

            if not stats or self.source not in stats:
                return 0.0

            try:
                return float(stats[self.source][0]["change"])
            except:
                return 0.0

        # Realer Verbrauch 1. → jetzt
        real_current = await self.hass.async_add_executor_job(
            get_stats, month_start, dt
        )

        #
        # ---- DAILY AVERAGE ----
        #
        day = dt.day
        avg = real_current / (day - 1) if day > 1 and real_current > 0 else 0.0

        #
        # ---- FORECAST FÜR AKTUELLEN MONAT ----
        #
        _, month_end = month_range(dt)
        remaining_days = month_end.day - (day - 1)
        forecast_current = real_current + avg * remaining_days

        #
        # ---- MONATSWERTE (VERGANGENHEIT, GEGENWART, ZUKUNFT) ----
        #
        months = {}

        for m in range(1, 13):
            # Vergangene Monate → echte Statistik
            if m < dt.month:
                past_dt = dt.replace(month=m, day=1)
                start, end = month_range(past_dt)

                val = await self.hass.async_add_executor_job(
                    get_stats, start, end
                )
                months[m] = val

            # Aktueller Monat → Forecast
            elif m == dt.month:
                months[m] = forecast_current

            # Zukunft → Skaliert nach Heizlastfaktor
            else:
                fc_now = HEAT_LOAD_FACTORS.get(dt.month, 1)
                fc_target = HEAT_LOAD_FACTORS.get(m, 1)

                if fc_now > 0:
                    months[m] = real_current * fc_target / fc_now
                else:
                    months[m] = 0.0

        #
        # ---- JAHRESGESAMT ----
        #
        year_total = sum(months.values())

        #
        # ---- KOORDINATOR-DATEN ----
        #
        return {
            "real": real_current,
            "avg": avg,
            "forecast_current": forecast_current,
            "months": months,
            "year": year_total,
        }