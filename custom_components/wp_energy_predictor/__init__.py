from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_PRICE_PER_KWH, CONF_SENSOR, DOMAIN
from .coordinator import WPEnergyPredictorCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})

    sensor_id = entry.options.get(CONF_SENSOR, entry.data[CONF_SENSOR])
    price = entry.options.get(
        CONF_PRICE_PER_KWH, entry.data.get(CONF_PRICE_PER_KWH, 0.0)
    )
    coordinator = WPEnergyPredictorCoordinator(hass, sensor_id, price_per_kwh=price)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady(str(err)) from err

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok and DOMAIN in hass.data:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
