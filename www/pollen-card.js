class PollenCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = {};
  }

  static get properties() {
    return {
      hass: {},
      config: {}
    };
  }

  setConfig(config) {
    if (!config) {
      throw new Error('Invalid configuration');
    }
    
    this._config = {
      title: config.title || 'Pollen (NO)',
      show_forecast: config.show_forecast !== false,
      show_levels: config.show_levels !== false,
      show_thresholds: config.show_thresholds !== false,
      entities: config.entities || [],
      region: config.region || '',
      ...config
    };
    
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  get hass() {
    return this._hass;
  }

  render() {
    if (!this._hass || !this._config) return;

    const pollenSensors = this.getPollenSensors();
    const forecastSensor = this.getForecastSensor();

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
        
        .card {
          background: var(--ha-card-background, var(--card-background-color, white));
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, var(--shadow-elevation-2dp_-_box-shadow));
          padding: 16px;
          margin: 8px;
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
        
        .pollen-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 12px;
          margin-bottom: 16px;
        }
        
        .pollen-item {
          background: var(--card-background-color, white);
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          padding: 12px;
          display: flex;
          align-items: center;
          justify-content: space-between;
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
          width: 20px;
          height: 20px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
          font-size: 0.8em;
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
        }
        
        .forecast-text {
          color: var(--secondary-text-color);
          line-height: 1.4;
        }
        
        .no-data {
          text-align: center;
          color: var(--secondary-text-color);
          padding: 20px;
        }
        
        .last-updated {
          font-size: 0.8em;
          color: var(--secondary-text-color);
          text-align: center;
          margin-top: 16px;
        }
        
        .icon {
          margin-right: 8px;
        }
      </style>
      
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">
            <ha-icon icon="mdi:flower-pollen" class="icon"></ha-icon>
            ${this._config.title}
          </h2>
        </div>
        
        ${pollenSensors.length > 0 ? `
          <div class="pollen-grid">
            ${pollenSensors.map(sensor => this.renderPollenItem(sensor)).join('')}
          </div>
        ` : `
          <div class="no-data">
            <ha-icon icon="mdi:alert-circle-outline"></ha-icon>
            <p>No active pollen data available</p>
          </div>
        `}
        
        ${this._config.show_forecast && forecastSensor ? `
          <div class="forecast-section">
            <h3 class="forecast-title">
              <ha-icon icon="mdi:weather-partly-cloudy" class="icon"></ha-icon>
              Forecast
            </h3>
            <div class="forecast-text">${forecastSensor.state}</div>
          </div>
        ` : ''}
        
        ${this.getLastUpdated() ? `
          <div class="last-updated">
            Last updated: ${this.getLastUpdated()}
          </div>
        ` : ''}
      </div>
    `;
  }

  renderPollenItem(sensor) {
    const attributes = sensor.attributes || {};
    const level = sensor.state || 0;
    const levelName = attributes.level_name || 'Unknown';
    const levelThreshold = attributes.level_threshold || '';
    const color = attributes.color || '#cccccc';
    const pollenType = attributes.pollen_type || 'unknown';

    return `
      <div class="pollen-item">
        <div class="pollen-info">
          <div class="pollen-name">${pollenType}</div>
          ${this._config.show_levels ? `
            <div class="pollen-details">Level: ${levelName}</div>
          ` : ''}
          ${this._config.show_thresholds ? `
            <div class="pollen-details">Range: ${levelThreshold} grains/m³</div>
          ` : ''}
        </div>
        <div class="pollen-level">
          <div class="level-indicator" style="background-color: ${color};">
            ${level}
          </div>
          <div class="level-text">${levelName}</div>
        </div>
      </div>
    `;
  }

  getPollenSensors() {
    const sensors = [];
    
    // If specific entities are configured, use those
    if (this._config.entities && this._config.entities.length > 0) {
      this._config.entities.forEach(entityId => {
        const entity = this._hass.states[entityId];
        if (entity && entity.attributes.pollen_type) {
          sensors.push(entity);
        }
      });
    } else {
      // Otherwise, find all pollen sensors automatically
      Object.keys(this._hass.states).forEach(entityId => {
        const entity = this._hass.states[entityId];
        if (entity && 
            entityId.startsWith('sensor.pollen_') && 
            !entityId.includes('_forecast') &&
            entity.attributes.pollen_type &&
            entity.state > 0) {
          sensors.push(entity);
        }
      });
    }
    
    // Sort by pollen type name
    return sensors.sort((a, b) => {
      const aType = a.attributes.pollen_type || '';
      const bType = b.attributes.pollen_type || '';
      return aType.localeCompare(bType);
    });
  }

  getForecastSensor() {
    // Look for forecast sensor
    const forecastEntityId = this._config.forecast_entity || 
                            Object.keys(this._hass.states).find(id => 
                              id.includes('pollen') && id.includes('forecast'));
    
    if (forecastEntityId) {
      return this._hass.states[forecastEntityId];
    }
    
    return null;
  }

  getLastUpdated() {
    const pollenSensors = this.getPollenSensors();
    if (pollenSensors.length > 0) {
      const lastUpdated = pollenSensors[0].attributes.last_updated;
      if (lastUpdated) {
        return new Date(lastUpdated).toLocaleString();
      }
    }
    return null;
  }

  getCardSize() {
    const pollenSensors = this.getPollenSensors();
    let size = 2; // Base size for header
    
    if (pollenSensors.length > 0) {
      size += Math.ceil(pollenSensors.length / 2); // Grid layout
    }
    
    if (this._config.show_forecast && this.getForecastSensor()) {
      size += 2; // Forecast section
    }
    
    return size;
  }
}

customElements.define('pollen-card', PollenCard);

// Register the card with the card picker
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'pollen-card',
  name: 'Pollen Card',
  description: 'A card for displaying pollen data from the Pollen integration',
  preview: true,
  documentationURL: 'https://github.com/sollie/pollendata'
});

// Add to Lovelace card picker
if (window.loadCardHelpers) {
  window.loadCardHelpers().then(() => {
    if (window.customCards) {
      window.customCards.push({
        type: 'pollen-card',
        name: 'Pollen Card',
        description: 'Display pollen data with color-coded levels'
      });
    }
  });
}