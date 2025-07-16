# Norwegian Pollen Data Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

A Home Assistant custom integration that fetches **Norwegian pollen data** and displays it in a beautiful custom card.

> **⚠️ DISCLAIMER**: This is an **unofficial** project and is **not affiliated** with NAAF (Norges Astma- og Allergiforbund / Norwegian Asthma and Allergy Association). This integration independently fetches publicly available data from their website for personal use only.

> **📍 Geographic Coverage**: This integration provides pollen data specifically for **Norway** regions only. The data is sourced from the Norwegian Asthma and Allergy Association (NAAF) via [www.naaf.no/pollenvarsel](https://www.naaf.no/pollenvarsel).

## Prerequisites

### Required: Pollendata Service

You need a running instance of the **[pollendata service](https://github.com/sollie/pollendata)** (separate project), which:

- Fetches pollen data from Norwegian sources ([www.naaf.no/pollenvarsel](https://www.naaf.no/pollenvarsel))
- Provides REST APIs for Norwegian regions
- Can run locally, on a remote server, or use a public instance

### Running the Service

**Option 1: Local Docker (Recommended for testing):**
```bash
docker run -p 8080:8080 sollie/pollendata:latest
```

**Option 2: Private server hosting:**
- Host the service on your own private server/network
- Use an existing public instance hosted by others
- Configure hostname to point to the private/public service

**Option 3: Cloud deployment:**
- Deploy to cloud platforms (AWS, Google Cloud, etc.)
- Use container orchestration (Kubernetes, Docker Swarm)
- Configure with appropriate security and access controls

**GitHub repository**: [sollie/pollendata](https://github.com/sollie/pollendata)

### Geographic Limitations

- **✅ Supported**: 12 Norwegian regions as defined by NAAF (see available regions below)
- **❌ Not supported**: Other countries or regions outside Norway
- **Data source**: Norwegian Asthma and Allergy Association (NAAF) via [www.naaf.no/pollenvarsel](https://www.naaf.no/pollenvarsel)

## Features

- **Norwegian pollen regions** - Support for all Norwegian regions with pollen monitoring
- **Configurable hostname and region** - Connect to your pollendata service
- **Active pollen filtering** - Only shows pollen types with data (level > 0)
- **Optional pollen type filtering** - Monitor specific pollen types
- **Color-coded severity levels** - Visual indication of pollen levels (0-4)
- **Forecast support** - Display text forecasts if available
- **Custom Lovelace card** - Beautiful card with grid layout and color indicators
- **Automatic updates** - Polls data every 30 minutes
- **Proper error handling** - Graceful handling of connection issues

## Installation

### Method 1: HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=sollie&repository=ha-pollen-no&category=integration)

1. Ensure you have [HACS](https://hacs.xyz/) installed
2. Add this repository as a custom repository in HACS:
   - Go to HACS > Integrations
   - Click the three dots in the top right corner
   - Select "Custom repositories"
   - Add `https://github.com/sollie/ha-pollen-no` as an Integration
3. Search for "Pollen (NO)" in HACS and install it
4. Restart Home Assistant
5. Go to Configuration > Integrations and add the "Pollen (NO)" integration

### Method 2: Manual Installation

1. Copy the `custom_components/pollen_no` folder to your Home Assistant's `custom_components` directory
2. Copy the `www/pollen-card.js` file to your Home Assistant's `www` directory
3. Restart Home Assistant
4. Go to Configuration > Integrations and add the "Pollen (NO)" integration

## Project Structure

This Home Assistant integration is separate from the backend service:

- **Backend Service**: [sollie/pollendata](https://github.com/sollie/pollendata) - Go service that fetches data
- **HA Integration**: [sollie/ha-pollen-no](https://github.com/sollie/ha-pollen-no) - This Python integration for Home Assistant

## Configuration

### Integration Setup

1. Go to **Configuration** > **Integrations**
2. Click the **+ Add Integration** button
3. Search for "Pollen (NO)"
4. Enter your pollendata service hostname (examples below)
5. Select your region from the available options
6. Click **Submit**

### Hostname Examples:
- **Local Docker**: `localhost:8080`
- **Private server**: `192.168.1.100:8080` or `my-home-server.local:8080`
- **Public instance**: `pollen-api.someservice.com`
- **Cloud deployment**: `my-pollen-service.herokuapp.com`

### Options Configuration

After setting up the integration, you can configure additional options:

1. Go to **Configuration** > **Integrations**
2. Find your Pollen (NO) integration
3. Click **Configure**
4. Select specific pollen types to monitor (optional)

## Custom Card Setup

### Step 1: Add the Card Resource

1. Go to **Configuration** > **Lovelace Dashboards** > **Resources**
2. Add a new resource:
   - **URL**: `/local/pollen-card.js`
   - **Resource type**: JavaScript module

### Step 2: Add the Card to Your Dashboard

#### Basic Configuration

```yaml
type: custom:pollen-card
title: "Pollen Data"
```

#### Advanced Configuration

```yaml
type: custom:pollen-card
title: "Pollen Levels"
show_forecast: true
show_levels: true
show_thresholds: true
entities:
  - sensor.pollen_birch
  - sensor.pollen_grass
  - sensor.pollen_alder
forecast_entity: sensor.pollen_forecast
```

### Card Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `title` | string | "Pollen (NO)" | Card title |
| `show_forecast` | boolean | true | Show forecast section |
| `show_levels` | boolean | true | Show level names (Low, Moderate, etc.) |
| `show_thresholds` | boolean | true | Show pollen count thresholds |
| `entities` | list | auto-detect | Specific pollen sensor entities |
| `forecast_entity` | string | auto-detect | Forecast sensor entity |

## Pollen Types

The integration monitors the following pollen types as available from the Norwegian Asthma and Allergy Association (NAAF):

| English Name | Norwegian Name | Sensor ID |
|-------------|----------------|-----------|
| Alder | Or | `sensor.pollen_alder` |
| Hazel | Hassel | `sensor.pollen_hazel` |
| Willow | Salix | `sensor.pollen_willow` |
| Birch | Bjørk | `sensor.pollen_birch` |
| Grass | Gress | `sensor.pollen_grass` |
| Mugwort | Burot | `sensor.pollen_mugwort` |

> **Note**: Only pollen types with active data (level > 0) will create sensors in Home Assistant.

## Sensors

The integration creates the following sensors:
- `sensor.pollen_alder` - Alder pollen level (Or)
- `sensor.pollen_hazel` - Hazel pollen level (Hassel)
- `sensor.pollen_willow` - Willow pollen level (Salix)
- `sensor.pollen_birch` - Birch pollen level (Bjørk)
- `sensor.pollen_grass` - Grass pollen level (Gress)
- `sensor.pollen_mugwort` - Mugwort pollen level (Burot)

### Forecast Sensor
- `sensor.pollen_forecast` - Text forecast (if available)

## Pollen Levels

The integration uses a 0-4 scale for pollen levels:

| Level | Name | Range (grains/m³) | Color |
|-------|------|-------------------|-------|
| 0 | None | 0 | Green |
| 1 | Low | 1-9 | Yellow |
| 2 | Moderate | 10-99 | Orange |
| 3 | Heavy | 100-999 | Red |
| 4 | Extreme | 1000+ | Purple |

## Sensor Attributes

Each pollen sensor provides these attributes:

- `level_name` - Human-readable level name
- `level_threshold` - Pollen count range
- `color` - Hex color code for the level
- `pollen_type` - Type of pollen
- `region` - Geographic region
- `last_updated` - Last update timestamp

## Pollendata Service Requirements

This integration requires a running [pollendata](https://github.com/sollie/pollendata) service that:

- **Fetches Norwegian pollen data** from [www.naaf.no/pollenvarsel](https://www.naaf.no/pollenvarsel)
- **Provides REST APIs** for Norwegian regions only
- **Can be hosted anywhere** - locally, on a remote server, or using a public instance accessible to Home Assistant

### API Endpoints:
- `/regions` - Available Norwegian regions
- `/pollen/{region}` - Pollen data for Norwegian region
- `/forecast/{region}` - Forecast text for Norwegian region
- `/combined/{region}` - Combined data and forecast

### Available Norwegian Regions:
Based on [www.naaf.no/pollenvarsel](https://www.naaf.no/pollenvarsel):
- **Østlandet med Oslo** - Eastern Norway with Oslo
- **Sørlandet** - Southern Norway
- **Rogaland** - Rogaland county
- **Hordaland** - Hordaland county
- **Sogn og Fjordane** - Sogn og Fjordane county
- **Møre og Romsdal** - Møre og Romsdal county
- **Indre Østlandet** - Inner Eastern Norway
- **Sentrale fjellstrøk i Sør-Norge** - Central mountain areas in Southern Norway
- **Trøndelag** - Trøndelag county
- **Nordland** - Nordland county
- **Troms** - Troms county
- **Finnmark** - Finnmark county

> **💡 Tip**: You can verify current available regions by visiting [www.naaf.no/pollenvarsel](https://www.naaf.no/pollenvarsel) directly.

## Troubleshooting

### Common Issues

1. **Cannot connect to service**
   - Verify the hostname and port are correct
   - Ensure the pollendata service is running and accessible
   - Check firewall settings (both local and remote if using public hosting)
   - Test connectivity: `curl http://your-hostname/regions`

2. **No sensors created**
   - Verify the Norwegian region has active pollen data
   - Check Home Assistant logs for errors
   - Ensure the pollendata service returns valid data

3. **Card not displaying**
   - Verify the card resource is properly added
   - Check browser console for JavaScript errors
   - Ensure the card configuration is correct

4. **Region not available**
   - Check that you're using a valid Norwegian region name
   - Verify the pollendata service is fetching current data from NAAF

5. **Public instance connection issues**
   - Ensure the public instance supports HTTPS if Home Assistant requires it
   - Check that the public instance has CORS configured properly
   - Verify the public instance is running the correct version of pollendata service

### Debug Logging

Add to your `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.pollen_no: debug
```

## Development

### Project Structure

```
custom_components/pollen_no/
├── __init__.py          # Integration entry point
├── manifest.json        # Integration metadata
├── config_flow.py       # Configuration UI
├── coordinator.py       # Data update coordinator
├── sensor.py           # Sensor platform
├── api.py              # API client
├── const.py            # Constants
└── strings.json        # Translations

www/
└── pollen-card.js      # Custom Lovelace card
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Related Projects

- [pollendata](https://github.com/sollie/pollendata) - The backend service for fetching pollen data

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/sollie/ha-pollen-no.svg?style=for-the-badge
[commits]: https://github.com/sollie/ha-pollen-no/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/sollie/ha-pollen-no.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/sollie/ha-pollen-no.svg?style=for-the-badge
[releases]: https://github.com/sollie/ha-pollen-no/releases
