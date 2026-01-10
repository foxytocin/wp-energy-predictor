from datetime import datetime, timedelta
from datetime import datetime, timedelta
from homeassistant.components import history
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


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

        def get_month_stats(hass, entity_id, year, month):
            """Return energy consumption for a given month using history API (HA 2026.1)."""

            # Monat starten
            start = datetime(year, month, 1)

            # Ersten Tag des nächsten Monats bestimmen
            if month == 12:
                end = datetime(year + 1, 1, 1)
            else:
                end = datetime(year, month + 1, 1)

            # Daten aus dem Recorder-History-System holen
            states = history.get_significant_states(
                hass=hass,
                start_time=start,
                end_time=end,
                entity_ids=[entity_id],
                significant_changes_only=False,
            )

            states = states.get(entity_id)

            if not states or len(states) < 2:
                return 0.0

            # Erstes & letztes State-Objekt
            first = float(states[0].state or 0)
            last  = float(states[-1].state or 0)

            # Monatsverbrauch berechnen
            return max(last - first, 0.0)

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