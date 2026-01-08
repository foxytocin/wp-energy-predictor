
import os

DASH_PATH="/config/wp_forecast_dashboard.yaml"

DASH_YAML="""
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

    async def create(call):
        with open(DASH_PATH,"w") as f:
            f.write(DASH_YAML)
        hass.components.lovelace.create_dashboard(
            url_path="wp-forecast",
            mode="yaml",
            filename=DASH_PATH,
            title="WP Forecast",
            icon="mdi:chart-bar"
        )

    hass.services.async_register("wp_energy_predictor","create_dashboard",create)
