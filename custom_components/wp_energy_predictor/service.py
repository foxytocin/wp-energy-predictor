import logging

_LOGGER = logging.getLogger(__name__)

DASH_YAML = """
title: WP Forecast
views:
  - title: Forecast
    cards:
      - type: vertical-stack
        cards:
          - type: custom:apexcharts-card
            header:
              show: true
              title: WP Monatsverbrauch (Heizen + Warmwasser)
            chart_type: line
            stacked: true
            graph_span: 366d
            span:
              start: year
            apex_config:
              chart:
                type: bar
              stroke:
                width: 0
              xaxis:
                type: datetime
                tickAmount: 12
                labels:
                  format: MMM
              plotOptions:
                bar:
                  columnWidth: 60%
                  dataLabels:
                    position: top
              dataLabels:
                enabled: false
            series:
              - entity: sensor.fms_wp_current_month_real
                name: Heizen (Real) (kWh)
                type: column
                data_generator: |
                  const year = start.getFullYear();
                  const now = new Date();
                  const currentMonth = now.getMonth() + 1;
                  const num = (eid) => {
                    const s = hass.states[eid];
                    const v = s ? Number.parseFloat(s.state) : null;
                    return Number.isFinite(v) ? v : null;
                  };
                  const points = [];
                  for (let m = 1; m <= 12; m++) {
                    let v = null;
                    if (m < currentMonth) v = num(`sensor.fms_wp_month_${m}`);
                    else if (m === currentMonth) v = num('sensor.fms_wp_current_month_real');
                    else v = 0;
                    points.push([new Date(year, m - 1, 1).getTime(), v]);
                  }
                  return points;
              - entity: sensor.fms_wp_current_month_forecast
                name: Heizen (Prognose) (kWh)
                type: column
                show:
                  legend_value: false
                data_generator: |
                  const year = start.getFullYear();
                  const now = new Date();
                  const currentMonth = now.getMonth() + 1;
                  const num = (eid) => {
                    const s = hass.states[eid];
                    const v = s ? Number.parseFloat(s.state) : null;
                    return Number.isFinite(v) ? v : null;
                  };
                  const points = [];
                  for (let m = 1; m <= 12; m++) {
                    let v = null;
                    if (m < currentMonth) v = 0;
                    else if (m === currentMonth) {
                      const real = num('sensor.fms_wp_current_month_real') ?? 0;
                      const fc = num('sensor.fms_wp_current_month_forecast');
                      v = fc == null ? null : Math.max(0, fc - real);
                    } else {
                      v = num(`sensor.fms_wp_month_${m}`);
                    }
                    points.push([new Date(year, m - 1, 1).getTime(), v]);
                  }
                  return points;
              - entity: sensor.fms_ww_current_month_real
                name: Warmwasser (Real) (kWh)
                type: column
                data_generator: |
                  const year = start.getFullYear();
                  const now = new Date();
                  const currentMonth = now.getMonth() + 1;
                  const num = (eid) => {
                    const s = hass.states[eid];
                    const v = s ? Number.parseFloat(s.state) : null;
                    return Number.isFinite(v) ? v : null;
                  };
                  const points = [];
                  for (let m = 1; m <= 12; m++) {
                    let v = null;
                    if (m < currentMonth) v = num(`sensor.fms_ww_month_${m}`);
                    else if (m === currentMonth) v = num('sensor.fms_ww_current_month_real');
                    else v = 0;
                    points.push([new Date(year, m - 1, 1).getTime(), v]);
                  }
                  return points;
              - entity: sensor.fms_ww_current_month_forecast
                name: Warmwasser (Prognose) (kWh)
                type: column
                show:
                  legend_value: false
                data_generator: |
                  const year = start.getFullYear();
                  const now = new Date();
                  const currentMonth = now.getMonth() + 1;
                  const num = (eid) => {
                    const s = hass.states[eid];
                    const v = s ? Number.parseFloat(s.state) : null;
                    return Number.isFinite(v) ? v : null;
                  };
                  const points = [];
                  for (let m = 1; m <= 12; m++) {
                    let v = null;
                    if (m < currentMonth) v = 0;
                    else if (m === currentMonth) {
                      const real = num('sensor.fms_ww_current_month_real') ?? 0;
                      const fc = num('sensor.fms_ww_current_month_forecast');
                      v = fc == null ? null : Math.max(0, fc - real);
                    } else {
                      v = num(`sensor.fms_ww_month_${m}`);
                    }
                    points.push([new Date(year, m - 1, 1).getTime(), v]);
                  }
                  return points;
          - type: entities
            entities:
              - entity: sensor.fms_wp_year_forecast
                name: "⚡ Jahresprognose"
                icon: mdi:lightning-bolt
              - entity: sensor.fms_wp_year_cost_forecast
                name: "💰 Jahreskosten (Prognose)"
                icon: mdi:currency-eur
              - entity: sensor.fms_ww_year_forecast
                name: "🚿 Warmwasser Jahresprognose"
                icon: mdi:water-boiler
              - entity: sensor.fms_ww_year_cost_forecast
                name: "💰 Warmwasser Jahreskosten (Prognose)"
                icon: mdi:currency-eur
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
