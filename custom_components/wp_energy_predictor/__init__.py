from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_PRICE_PER_KWH,
    CONF_SENSOR,
    CONF_WW_SENSOR,
    DOMAIN,
    WARM_WATER_LOAD_FACTORS,
)
from .coordinator import WPEnergyPredictorCoordinator
from .service import async_setup_services


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})

    sensor_id = entry.options.get(CONF_SENSOR, entry.data[CONF_SENSOR])
    ww_sensor_id = entry.options.get(CONF_WW_SENSOR, entry.data.get(CONF_WW_SENSOR))
    price = entry.options.get(
        CONF_PRICE_PER_KWH, entry.data.get(CONF_PRICE_PER_KWH, 0.30)
    )

    heat_coordinator = WPEnergyPredictorCoordinator(
        hass,
        sensor_id,
        price_per_kwh=price,
        coordinator_name=f"{DOMAIN}_heat",
    )
    ww_coordinator = (
        WPEnergyPredictorCoordinator(
            hass,
            ww_sensor_id,
            price_per_kwh=price,
            load_factors=WARM_WATER_LOAD_FACTORS,
            coordinator_name=f"{DOMAIN}_warmwater",
        )
        if ww_sensor_id
        else None
    )
    try:
        await heat_coordinator.async_config_entry_first_refresh()
        if ww_coordinator is not None:
            await ww_coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady(str(err)) from err

    hass.data[DOMAIN][entry.entry_id] = {"heat": heat_coordinator, "ww": ww_coordinator}
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    await async_setup_services(hass)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok and DOMAIN in hass.data:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
