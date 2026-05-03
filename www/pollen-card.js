import {
  LitElement,
  html,
  css,
} from "https://unpkg.com/lit-element@4.1.1/lit-element.js?module";

class PollenCard extends LitElement {
  static get properties() {
    return {
      hass: { attribute: false },
      config: { attribute: false },
      _expanded: { state: true },
    };
  }

  constructor() {
    super();
    this._expanded = {};
  }

  static get styles() {
    return css`
      :host {
        display: block;
      }
      .card {
        background: var(--ha-card-background, var(--card-background-color, white));
        border-radius: var(--ha-card-border-radius, 12px);
        box-shadow: var(--ha-card-box-shadow, var(--shadow-elevation-2dp_-_box-shadow));
        padding: 16px;
      }
      .card-header {
        display: flex;
        align-items: center;
        margin-bottom: 16px;
      }
      .card-title {
        font-size: 1.2em;
        font-weight: 500;
        margin: 0;
        color: var(--primary-text-color);
      }
      ha-icon.title-icon {
        margin-right: 8px;
      }
      .pollen-grid {
        display: flex;
        flex-direction: column;
        gap: 4px;
        margin-bottom: 16px;
      }
      .pollen-info {
        display: flex;
        flex-direction: column;
      }
      .pollen-name {
        font-weight: 500;
        color: var(--primary-text-color);
        margin-bottom: 4px;
        text-transform: capitalize;
      }
      .pollen-details {
        font-size: 0.9em;
        color: var(--secondary-text-color);
      }
      .pollen-level {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .level-indicator {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 0.85em;
        flex-shrink: 0;
      }
      .level-text {
        font-weight: 500;
        color: var(--primary-text-color);
      }
      .forecast-section {
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid var(--divider-color);
      }
      .forecast-title {
        font-size: 1.1em;
        font-weight: 500;
        margin-bottom: 8px;
        color: var(--primary-text-color);
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .forecast-text {
        color: var(--secondary-text-color);
        line-height: 1.4;
      }
      .no-data {
        text-align: center;
        color: var(--secondary-text-color);
        padding: 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
      }
      .last-updated {
        font-size: 0.8em;
        color: var(--secondary-text-color);
        text-align: center;
        margin-top: 16px;
      }
      .pollen-item {
        background: var(--card-background-color, white);
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 4px;
      }
      .pollen-item-row {
        padding: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        cursor: pointer;
        user-select: none;
      }
      .pollen-item-row:hover {
        background: var(--secondary-background-color, rgba(0,0,0,0.04));
      }
      .forecast-days {
        border-top: 1px solid var(--divider-color);
        background: var(--secondary-background-color, rgba(0,0,0,0.02));
      }
      .forecast-day-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 12px;
        font-size: 0.9em;
        color: var(--secondary-text-color);
      }
      .forecast-day-row + .forecast-day-row {
        border-top: 1px solid var(--divider-color);
      }
      .forecast-day-date {
        flex: 1;
      }
      .expand-icon {
        font-size: 0.8em;
        color: var(--secondary-text-color);
        margin-left: 8px;
        transition: transform 0.2s;
      }
      .expand-icon.open {
        transform: rotate(180deg);
      }
    `;
  }

  setConfig(config) {
    if (!config) {
      throw new Error("Invalid configuration");
    }
    this.config = {
      title: "Pollen (NO)",
      show_forecast: true,
      show_levels: true,
      show_thresholds: true,
      entities: [],
      region: "",
      ...config,
    };
  }

  _getPollenSensors() {
    if (!this.hass) return [];

    if (this.config.entities && this.config.entities.length > 0) {
      return this.config.entities
        .map((id) => this.hass.states[id])
        .filter((s) => s && s.attributes.pollen_type !== undefined);
    }

    return Object.values(this.hass.states)
      .filter(
        (s) =>
          s.entity_id.startsWith("sensor.pollen_") &&
          !s.entity_id.includes("_forecast") &&
          s.attributes.pollen_type !== undefined
      )
      .sort((a, b) =>
        (a.attributes.pollen_type || "").localeCompare(
          b.attributes.pollen_type || ""
        )
      );
  }

  _getForecastSensor() {
    if (!this.hass) return null;
    const id =
      this.config.forecast_entity ||
      Object.keys(this.hass.states).find(
        (k) => k.startsWith("sensor.pollen_") && k.includes("forecast")
      );
    return id ? this.hass.states[id] : null;
  }

  _levelColor(level) {
    const colors = {
      0: "#4CAF50",
      1: "#FFEB3B",
      2: "#FF9800",
      3: "#F44336",
      4: "#9C27B0",
    };
    return colors[Number(level)] ?? "#cccccc";
  }

  _toggleExpanded(key) {
    this._expanded = { ...this._expanded, [key]: !this._expanded[key] };
  }

  _formatDate(dateStr) {
    const d = new Date(dateStr + "T00:00:00");
    return d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
  }

  _renderPollenItem(sensor) {
    const attrs = sensor.attributes || {};
    const level = sensor.state;
    const levelName = attrs.level_name || "Unknown";
    const levelThreshold = attrs.level_threshold || "";
    const pollenType = attrs.pollen_type || sensor.entity_id;
    const color = this._levelColor(level);
    const forecast = Array.isArray(attrs.forecast) ? attrs.forecast : [];
    const key = sensor.entity_id;
    const expanded = !!this._expanded[key];

    return html`
      <div class="pollen-item">
        <div class="pollen-item-row" @click=${() => this._toggleExpanded(key)}>
          <div class="pollen-info">
            <div class="pollen-name">${pollenType}</div>
            ${this.config.show_levels
              ? html`<div class="pollen-details">Level: ${levelName}</div>`
              : ""}
            ${this.config.show_thresholds && levelThreshold
              ? html`<div class="pollen-details">Range: ${levelThreshold} grains/m³</div>`
              : ""}
          </div>
          <div class="pollen-level">
            <div class="level-indicator" style="background-color: ${color};">${level}</div>
            <div class="level-text">${levelName}</div>
            ${forecast.length > 0
              ? html`<span class="expand-icon ${expanded ? "open" : ""}">▼</span>`
              : ""}
          </div>
        </div>
        ${expanded && forecast.length > 0
          ? html`
              <div class="forecast-days">
                ${forecast.map((f) => html`
                  <div class="forecast-day-row">
                    <span class="forecast-day-date">${this._formatDate(f.date)}</span>
                    <div class="pollen-level">
                      <div class="level-indicator" style="background-color: ${this._levelColor(f.level)}; width:22px; height:22px; font-size:0.8em;">${f.level}</div>
                      <span>${(this._levelName(f.level))}</span>
                    </div>
                  </div>
                `)}
              </div>
            `
          : ""}
      </div>
    `;
  }

  _levelName(level) {
    const names = { 0: "None", 1: "Low", 2: "Moderate", 3: "High", 4: "Very High" };
    return names[Number(level)] ?? "Unknown";
  }

  render() {
    if (!this.hass || !this.config) return html``;

    const sensors = this._getPollenSensors();
    const forecast = this._getForecastSensor();
    const lastUpdated = sensors[0]?.attributes?.last_updated;

    return html`
      <div class="card">
        <div class="card-header">
          <ha-icon class="title-icon" icon="mdi:flower-pollen"></ha-icon>
          <h2 class="card-title">${this.config.title}</h2>
        </div>

        ${sensors.length > 0
          ? html`<div class="pollen-grid">
              ${sensors.map((s) => this._renderPollenItem(s))}
            </div>`
          : html`<div class="no-data">
              <ha-icon icon="mdi:alert-circle-outline"></ha-icon>
              <p>No pollen data available</p>
            </div>`}

        ${this.config.show_forecast && forecast
          ? html`
              <div class="forecast-section">
                <div class="forecast-title">
                  <ha-icon icon="mdi:weather-partly-cloudy"></ha-icon>
                  Forecast
                </div>
                <div class="forecast-text">${forecast.state}</div>
              </div>
            `
          : ""}

        ${lastUpdated
          ? html`<div class="last-updated">
              Last updated: ${new Date(lastUpdated).toLocaleString()}
            </div>`
          : ""}
      </div>
    `;
  }

  getCardSize() {
    const sensors = this._getPollenSensors();
    let size = 2;
    if (sensors.length > 0) size += Math.ceil(sensors.length / 2);
    if (this.config?.show_forecast && this._getForecastSensor()) size += 2;
    return size;
  }

  getGridOptions() {
    return {
      columns: 12,
      min_rows: 2,
    };
  }

  static getStubConfig() {
    return {
      title: "Pollen (NO)",
      show_forecast: true,
      show_levels: true,
      show_thresholds: true,
    };
  }
}

customElements.define("pollen-card", PollenCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "pollen-card",
  name: "Pollen Card",
  description: "Display Norwegian pollen data with color-coded levels",
  preview: true,
  documentationURL: "https://github.com/sollie/ha-pollen-no",
});
