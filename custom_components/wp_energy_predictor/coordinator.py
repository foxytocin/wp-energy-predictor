from __future__ import annotations

import calendar
import inspect
import logging
from datetime import datetime, timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.const import UnitOfEnergy
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_PRICE_PER_KWH, CONF_SENSOR, HEAT_LOAD_FACTORS


_LOGGER = logging.getLogger(__name__)


class WPEnergyPredictorCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, source_sensor: str, price_per_kwh: float = 0.0):
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )
        self.source = source_sensor
        self.price_per_kwh = float(price_per_kwh or 0.0)

    async def _async_update_data(self):
        """Fetch monthly values + current month real + forecast."""
        now = dt_util.now()
        year = now.year
        month = now.month
        tz = dt_util.DEFAULT_TIME_ZONE

        # This function is executed in the executor (mandatory for recorder access)
        def get_month_stats(year: int, month: int) -> float:
            start_local = datetime(year, month, 1, tzinfo=tz)
            if month == 12:
                end_local = datetime(year + 1, 1, 1, tzinfo=tz) - timedelta(seconds=1)
            else:
                end_local = datetime(year, month + 1, 1, tzinfo=tz) - timedelta(seconds=1)

            start = dt_util.as_utc(start_local)
            end = dt_util.as_utc(end_local)

            values_by_name = {
                "hass": self.hass,
                "start": start,
                "start_time": start,
                "end": end,
                "end_time": end,
                "statistic_ids": [self.source],
                "period": "month",
                "types": ["change"],
                "units": [UnitOfEnergy.KILO_WATT_HOUR],
                "unit": UnitOfEnergy.KILO_WATT_HOUR,
            }

            args: list[object] = []
            kwargs: dict[str, object] = {}
            for param in inspect.signature(statistics_during_period).parameters.values():
                if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                    continue
                if param.name not in values_by_name:
                    continue
                if param.kind == param.POSITIONAL_ONLY:
                    args.append(values_by_name[param.name])
                else:
                    kwargs[param.name] = values_by_name[param.name]

            stats = statistics_during_period(*args, **kwargs)

            if stats and self.source in stats:
                return float(stats[self.source][0]["change"])
            return 0.0

        # CALL RECORDER IN EXECUTOR (important!)
        real_current = await get_instance(self.hass).async_add_executor_job(
            get_month_stats, year, month
        )

        # Daily average
        if now.day > 1:
            daily_avg = real_current / (now.day - 1)
        else:
            daily_avg = 0.0

        days_in_month = calendar.monthrange(year, month)[1]
        remaining_days = days_in_month - (now.day - 1)
        forecast_current_value = real_current + daily_avg * remaining_days

        # Build dict of 12 months
        months = {}
        for m in range(1, 13):

            if m < month:
                # Past month → get real historical value
                months[m] = await get_instance(self.hass).async_add_executor_job(
                    get_month_stats, year, m
                )

            elif m == month:
                # Current month → forecast
                months[m] = forecast_current_value

            else:
                # Future → based on heat load factors
                fc_now = HEAT_LOAD_FACTORS[month]
                fc_target = HEAT_LOAD_FACTORS[m]
                months[m] = forecast_current_value * (fc_target / fc_now)

        forecast_current = months[month]
        year_forecast = sum(months.values())

        month_costs = {m: v * self.price_per_kwh for m, v in months.items()}
        year_cost_forecast = year_forecast * self.price_per_kwh

        return {
            "current_real": real_current,
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
