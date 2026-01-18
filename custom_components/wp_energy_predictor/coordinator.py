from __future__ import annotations

import calendar
import logging
from datetime import datetime, timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.const import UnitOfEnergy
from homeassistant.util import dt as dt_util

from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)


class WPEnergyPredictorCoordinator(DataUpdateCoordinator):
    def __init__(
        self,
        hass,
        source_sensor: str,
        *,
        price_per_kwh: float = 0.0,
        load_factors: dict[int, float] | None = None,
        month_corrections: dict[int, float] | None = None,
        coordinator_name: str | None = None,
    ):
        super().__init__(
            hass,
            logger=_LOGGER,
            name=coordinator_name or DOMAIN,
            update_interval=timedelta(minutes=5),
        )
        self.source = source_sensor
        self.price_per_kwh = float(price_per_kwh or 0.0)
        self._load_factors = load_factors or {}
        self._month_corrections = month_corrections or {}
        # Cache for past months to avoid repeated DB queries
        # A cached month value of None means "no statistics data for that month".
        self._cached_months: dict[int, float | None] = {}
        self._cache_year: int | None = None

    def _get_month_stats_sync(self, year: int, month: int) -> float | None:
        """Fetch monthly statistics from recorder (runs in executor)."""
        tz = dt_util.DEFAULT_TIME_ZONE
        start_local = datetime(year, month, 1, tzinfo=tz)
        if month == 12:
            end_local = datetime(year + 1, 1, 1, tzinfo=tz) - timedelta(seconds=1)
        else:
            end_local = datetime(year, month + 1, 1, tzinfo=tz) - timedelta(seconds=1)

        start = dt_util.as_utc(start_local)
        end = dt_util.as_utc(end_local)

        try:
            # Try modern API signature first (HA 2023.5+)
            stats = statistics_during_period(
                self.hass,
                start_time=start,
                end_time=end,
                statistic_ids=[self.source],
                period="month",
                units={"energy": UnitOfEnergy.KILO_WATT_HOUR},
                types={"change"},
            )
        except TypeError:
            # Fallback for older HA versions
            try:
                stats = statistics_during_period(
                    self.hass, start, end, [self.source], "month", None, {"change"}
                )
            except Exception as err:
                _LOGGER.warning("Failed to fetch statistics: %s", err)
                return None

        if stats and self.source in stats and stats[self.source]:
            return float(stats[self.source][0].get("change", 0) or 0)
        return None

    async def _async_update_data(self):
        """Fetch monthly values + current month real + forecast."""
        now = dt_util.now()
        year = now.year
        month = now.month

        # Invalidate cache on year change
        if self._cache_year != year:
            self._cached_months = {}
            self._cache_year = year

        # Fetch current month's real consumption
        real_current_raw = await get_instance(self.hass).async_add_executor_job(
            self._get_month_stats_sync, year, month
        )
        real_current = float(real_current_raw or 0.0)
        correction_current = float(self._month_corrections.get(month, 0.0) or 0.0)
        real_current_corrected = real_current + correction_current

        # Load and cache past months (only if not already cached)
        for m in range(1, month):
            if m not in self._cached_months:
                self._cached_months[m] = await get_instance(
                    self.hass
                ).async_add_executor_job(self._get_month_stats_sync, year, m)

        # Daily average calculation with fallback for first day of month
        if now.day > 1:
            daily_avg = real_current_corrected / (now.day - 1)
        else:
            # Fallback: use previous month's average
            prev_month = 12 if month == 1 else month - 1
            prev_year = year - 1 if month == 1 else year
            
            # Get previous month value (from cache or fetch)
            if prev_month in self._cached_months:
                prev_month_value = self._cached_months[prev_month]
            else:
                prev_month_value = await get_instance(self.hass).async_add_executor_job(
                    self._get_month_stats_sync, prev_year, prev_month
                )

            prev_days = calendar.monthrange(prev_year, prev_month)[1]
            daily_avg = (
                (
                    float(prev_month_value or 0.0)
                    + float(self._month_corrections.get(prev_month, 0.0) or 0.0)
                )
                / prev_days
                if prev_days > 0
                else 0.0
            )

        days_in_month = calendar.monthrange(year, month)[1]
        remaining_days = days_in_month - (now.day - 1)
        forecast_current_value = real_current_corrected + daily_avg * remaining_days

        fc_now = float(self._load_factors.get(month, 0.0) or 0.0)
        normalized_history: list[float] = []
        if fc_now:
            normalized_history.append(forecast_current_value / fc_now)

        # Use past months with real data (plus corrections) to refine base value
        for m in range(1, month):
            cached_value = self._cached_months.get(m)
            if cached_value is None:
                continue
            lf = float(self._load_factors.get(m, 0.0) or 0.0)
            if not lf:
                continue
            correction = float(self._month_corrections.get(m, 0.0) or 0.0)
            normalized_history.append((float(cached_value) + correction) / lf)

        if normalized_history:
            base_value = sum(normalized_history) / len(normalized_history)
        else:
            base_value = forecast_current_value / fc_now if fc_now else 0.0

        # Build dict of 12 months.
        # Past months use real recorder values where available; if statistics are missing,
        # we estimate using the load profile (e.g. warm-water factors).
        months: dict[int, float] = {}
        for m in range(1, 13):
            correction = float(self._month_corrections.get(m, 0.0) or 0.0)
            lf = float(self._load_factors.get(m, 0.0) or 0.0)
            if m < month:
                # Past month → use cached value
                cached_value = self._cached_months.get(m)
                if cached_value is None:
                    months[m] = base_value * lf + correction
                else:
                    months[m] = float(cached_value) + correction
            elif m == month:
                # Current month → forecast
                months[m] = forecast_current_value
            else:
                # Future → based on configured load factors (heating or warm water)
                months[m] = base_value * lf + correction

        forecast_current = months[month]
        year_forecast = sum(months.values())

        month_costs = {m: v * self.price_per_kwh for m, v in months.items()}
        year_cost_forecast = year_forecast * self.price_per_kwh

        return {
            "current_real": real_current_corrected,
            "daily_avg": daily_avg,
            "forecast_current": forecast_current,
            "year_forecast": year_forecast,
            "months": {m: round(v, 2) for m, v in months.items()},
            "price_per_kwh": self.price_per_kwh,
            "month_costs": {m: round(v, 2) for m, v in month_costs.items()},
            "year_cost_forecast": round(year_cost_forecast, 2),
        }

    def _get_month_bounds(self, dt: datetime):
        start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if dt.month == 12:
            end = dt.replace(year=dt.year + 1, month=1, day=1) - timedelta(seconds=1)
        else:
            end = dt.replace(month=dt.month + 1, day=1) - timedelta(seconds=1)
        return start, end
