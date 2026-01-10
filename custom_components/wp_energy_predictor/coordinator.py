from datetime import datetime, timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components.recorder import get_instance

from .const import HEAT_LOAD_FACTORS

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = 300  # 5 minutes


class WPEnergyPredictorCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, sensor_id: str):
        super().__init__(
            hass,
            _LOGGER,
            name="wp_energy_predictor",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.sensor_id = sensor_id

    async def _async_update_data(self):
        """Fetch statistics for all months + calculate forecast."""

        recorder = get_instance(self.hass)

        def get_month_stats(year: int, month: int):
            """Read total kWh for month using recorder.get_statistics()."""
            # Start of month
            start = datetime(year, month, 1)
            # End of month (exclusive)
            if month == 12:
                end = datetime(year + 1, 1, 1)
            else:
                end = datetime(year, month + 1, 1)

            stats = recorder.get_statistics(
                start_time=start,
                end_time=end,
                statistic_ids=[self.sensor_id],
                types=["change"],
            )

            if stats and self.sensor_id in stats:
                return stats[self.sensor_id][0]["change"]

            return 0.0

        now = datetime.now()
        current_month = now.month
        current_year = now.year

        # --- REAL CURRENT MONTH ---
        real_current = get_month_stats(current_year, current_month)

        # --- DAILY AVERAGE ---
        if now.day > 1:
            daily_avg = real_current / (now.day - 1)
        else:
            daily_avg = 0.0

        # --- FORECAST CURRENT MONTH ---
        days_in_month = (datetime(current_year, current_month + (1 if current_month < 12 else -11), 1)
                         - timedelta(days=1)).day
        remaining_days = days_in_month - (now.day - 1)

        forecast_current = real_current + remaining_days * daily_avg

        # --- CALCULATE ALL MONTHS ---
        months = {}

        for m in range(1, 13):
            if m < current_month:
                months[m] = get_month_stats(current_year, m)
            elif m == current_month:
                months[m] = forecast_current
            else:
                fc_now = HEAT_LOAD_FACTORS[current_month]
                fc_target = HEAT_LOAD_FACTORS[m]
                months[m] = forecast_current * (fc_target / fc_now)

        # --- YEAR FORECAST ---
        year_forecast = sum(months.values())

        return {
            "months": months,
            "current_real": real_current,
            "daily_avg": daily_avg,
            "forecast_current": forecast_current,
            "year_forecast": year_forecast,
        }