
from datetime import datetime, timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.util.dt import now
from .const import HEAT_LOAD_FACTORS, CONF_SENSOR

def get_month_range(dt):
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if dt.month == 12:
        nextm = dt.replace(year=dt.year + 1, month=1, day=1)
    else:
        nextm = dt.replace(month=dt.month + 1, day=1)
    return start, nextm - timedelta(seconds=1)

def get_month_stats(hass, ent, year, month):
    dt = datetime(year, month, 1)
    start, end = get_month_range(dt)
    stats = statistics_during_period(hass, start, end, [ent], "change")
    if stats and ent in stats:
        return float(stats[ent][0]["change"])
    return 0.0

async def async_setup_entry(hass, entry, async_add_entities):
    src = entry.data[CONF_SENSOR]
    entities = [
        DailyAverageSensor(hass, src),
        CurrentRealMonthSensor(hass, src),
        CurrentMonthForecastSensor(hass, src),
        YearForecastSensor(hass)
    ]
    for m in range(1, 13):
        entities.append(MonthSensor(hass, src, m))
    async_add_entities(entities)

class DailyAverageSensor(SensorEntity):
    _attr_name="FMS WP Daily Average"
    _attr_unique_id="fms_wp_daily_average"
    _attr_native_unit_of_measurement="kWh"
    def __init__(self,h,s):
        self.hass=h; self.s=s
    @property
    def native_value(self):
        t=now(); start,_=get_month_range(t)
        stats=statistics_during_period(self.hass,start,t,[self.s],"change")
        if not stats or self.s not in stats: return None
        real=float(stats[self.s][0]["change"])
        return round(real/(t.day-1),2) if t.day>1 else None

class CurrentRealMonthSensor(SensorEntity):
    _attr_name="FMS WP Current Month Real"
    _attr_unique_id="fms_wp_current_real"
    _attr_native_unit_of_measurement="kWh"
    def __init__(self,h,s):
        self.hass=h; self.s=s
    @property
    def native_value(self):
        t=now(); start,_=get_month_range(t)
        stats=statistics_during_period(self.hass,start,t,[self.s],"change")
        if stats and self.s in stats: return float(stats[self.s][0]["change"])
        return None

class CurrentMonthForecastSensor(SensorEntity):
    _attr_name="FMS WP Current Month Forecast"
    _attr_unique_id="fms_wp_current_forecast"
    _attr_native_unit_of_measurement="kWh"
    def __init__(self,h,s):
        self.hass=h; self.s=s
    @property
    def native_value(self):
        t=now()
        st_r=self.hass.states.get("sensor.fms_wp_current_real")
        st_avg=self.hass.states.get("sensor.fms_wp_daily_average")
        if not st_r or not st_avg: return None
        try:
            real=float(st_r.state); avg=float(st_avg.state)
        except: return None
        _,end=get_month_range(t)
        rem=end.day-(t.day-1)
        return round(real+avg*rem,2)

class MonthSensor(SensorEntity):
    _attr_native_unit_of_measurement="kWh"
    def __init__(self,h,s,m):
        self.hass=h; self.s=s; self.m=m
        self._attr_name=f"FMS WP Month {m}"
        self._attr_unique_id=f"fms_wp_month_{m}"
    @property
    def native_value(self):
        t=now(); cm=t.month
        st_r=self.hass.states.get("sensor.fms_wp_current_real")
        st_f=self.hass.states.get("sensor.fms_wp_current_forecast")
        if not st_r or not st_f: return None
        try:
            real=float(st_r.state); fc=float(st_f.state)
        except: return None
        if self.m < cm:
            return get_month_stats(self.hass,self.s,t.year,self.m)
        if self.m == cm:
            return fc
        fc_now=HEAT_LOAD_FACTORS[cm]; fc_t=HEAT_LOAD_FACTORS[self.m]
        return round(real*fc_t/fc_now,2) if fc_now>0 else 0.0

class YearForecastSensor(SensorEntity):
    _attr_name="FMS WP Year Forecast"
    _attr_unique_id="fms_wp_year_forecast"
    _attr_native_unit_of_measurement="kWh"
    def __init__(self,h): self.hass=h
    @property
    def native_value(self):
        total=0.0
        for m in range(1,13):
            st=self.hass.states.get(f"sensor.fms_wp_month_{m}")
            if st:
                try: total+=float(st.state)
                except: pass
        return round(total,2)
