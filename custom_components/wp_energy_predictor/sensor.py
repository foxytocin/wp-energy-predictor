
from homeassistant.components.sensor import SensorEntity
from .coordinator import WPDataCoordinator

async def async_setup_entry(hass, entry, async_add_entities):
    src = entry.options.get("source_sensor", entry.data["source_sensor"])
    coord=WPDataCoordinator(hass,src)
    await coord.async_config_entry_first_refresh()

    entities=[]
    entities.append(WPSimpleSensor(coord,"FMS WP Current Month Real","real","kWh"))
    entities.append(WPSimpleSensor(coord,"FMS WP Daily Average","avg","kWh"))
    entities.append(WPSimpleSensor(coord,"FMS WP Current Month Forecast","forecast_current","kWh"))
    entities.append(WPSimpleSensor(coord,"FMS WP Year Forecast","year","kWh"))

    for m in range(1,13):
        entities.append(WPMonthSensor(coord,m))

    async_add_entities(entities)

class WPSimpleSensor(SensorEntity):

    def __init__(self,coord,name,key,unit):
        self._attr_name=name
        self._attr_unique_id=name.replace(" ","_").lower()
        self.coord=coord
        self.key=key
        self._attr_native_unit_of_measurement=unit

    @property
    def native_value(self):
        return self.coord.data.get(self.key)

    @property
    def available(self):
        return self.coord.last_update_success

class WPMonthSensor(SensorEntity):

    def __init__(self,coord,month):
        self.coord=coord
        self.month=month
        self._attr_name=f"FMS WP Month {month}"
        self._attr_unique_id=f"fms_wp_month_{month}"
        self._attr_native_unit_of_measurement="kWh"

    @property
    def native_value(self):
        return self.coord.data["months"][self.month]

    @property
    def available(self):
        return self.coord.last_update_success
