import logging

_LOGGER = logging.getLogger(__name__)

DASH_YAML = """
title: WP Forecast
views:
  - title: Forecast
    cards:
      - type: custom:apexcharts-card
        header:
          title: Wärmepumpe Jahresprognose
          show: true
        all_series_config:
          type: column
        series:
          - entity: sensor.fms_wp_month_1
          - entity: sensor.fms_wp_month_2
          - entity: sensor.fms_wp_month_3
          - entity: sensor.fms_wp_month_4
          - entity: sensor.fms_wp_month_5
          - entity: sensor.fms_wp_month_6
          - entity: sensor.fms_wp_month_7
          - entity: sensor.fms_wp_month_8
          - entity: sensor.fms_wp_month_9
          - entity: sensor.fms_wp_month_10
          - entity: sensor.fms_wp_month_11
          - entity: sensor.fms_wp_month_12
"""


async def async_setup_services(hass):
    """Register custom services for the integration."""
    
    async def create_dashboard(call):
        """Create a YAML dashboard with the WP yearly forecast."""
        dash_path = hass.config.path("wp_forecast_dashboard.yaml")
        
        try:
            # Write dashboard YAML file
            await hass.async_add_executor_job(_write_dashboard_file, dash_path)
            
            # Register dashboard with Lovelace
            await hass.components.lovelace.async_create_dashboard(
                url_path="wp-forecast",
                mode="yaml",
                config={"filename": dash_path},
                title="WP Forecast",
                icon="mdi:chart-bar",
            )
            _LOGGER.info("Created WP Forecast dashboard at %s", dash_path)
        except Exception as err:
            _LOGGER.error("Failed to create dashboard: %s", err)

    hass.services.async_register("wp_energy_predictor", "create_dashboard", create_dashboard)


def _write_dashboard_file(path: str) -> None:
    """Write dashboard YAML file (runs in executor)."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(DASH_YAML)
