
import os
from homeassistant.core import HomeAssistant

DASH_PATH = "/config/wp_forecast_dashboard.yaml"

DASH_YAML = """
title: WP Forecast
views:
  - title: Forecast
    path: forecast
    cards:
      - type: custom:apexcharts-card
        header:
          title: Wärmepumpe Jahresprognose
          show: true
        graph_span: 12months
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

async def async_setup_services(hass: HomeAssistant):

    async def handle_create(call):
        # Check if ApexCharts is installed in Lovelace resources
        resources = hass.data.get("lovelace", {}).get("resources", [])

        apex_installed = any("apexcharts-card" in (res.get("url","") or "") for res in resources)

        if not apex_installed:
            hass.components.persistent_notification.async_create(
                "ApexCharts is not installed. Install via HACS: 'ApexCharts Card'",
                title="WP Energy Predictor"
            )

        # Write dashboard file
        with open(DASH_PATH, "w") as f:
            f.write(DASH_YAML)

        # Register dashboard (not auto-added to sidebar)
        hass.components.lovelace.create_dashboard(
            url_path="wp-forecast",
            mode="yaml",
            filename=DASH_PATH,
            title="WP Forecast",
            icon="mdi:chart-bar"
        )

    hass.services.async_register("wp_energy_predictor", "create_dashboard", handle_create)
