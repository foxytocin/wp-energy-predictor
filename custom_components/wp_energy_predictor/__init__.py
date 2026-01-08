from .service import async_setup_services
from .options_flow import WPEnergyPredictorOptionsFlow

async def async_setup_entry(hass, entry):
    await async_setup_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass, entry):
    await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    return True

def async_get_options_flow(config_entry):
    return WPEnergyPredictorOptionsFlow(config_entry)