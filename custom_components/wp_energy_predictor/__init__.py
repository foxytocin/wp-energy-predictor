
from .service import async_setup_services
from .options_flow import WPEnergyPredictorOptionsFlow

async def async_setup_entry(hass, entry):
    await async_setup_services(hass)
    return True

async def async_unload_entry(hass, entry):
    return True

def async_get_options_flow(config_entry):
    return WPEnergyPredictorOptionsFlow(config_entry)