"""Constants for the Pollen Data integration."""

DOMAIN = "pollen_no"

# Configuration keys
CONF_HOSTNAME = "hostname"
CONF_REGION = "region"
CONF_POLLEN_TYPES = "pollen_types"

# Default values
DEFAULT_HOSTNAME = "localhost:8080"
DEFAULT_SCAN_INTERVAL = 30  # minutes
DEFAULT_TIMEOUT = 30  # seconds

# API endpoints
API_REGIONS = "/regions"
API_POLLEN = "/pollen/{region}"
API_FORECAST = "/forecast/{region}"
API_COMBINED = "/combined/{region}"

# Pollen severity levels
POLLEN_LEVELS = {
    0: "None",
    1: "Low",
    2: "Moderate", 
    3: "Heavy",
    4: "Extreme"
}

# Pollen level thresholds (grains per m³)
POLLEN_THRESHOLDS = {
    0: "0",
    1: "1-9",
    2: "10-99",
    3: "100-999",
    4: "1000+"
}

# Norwegian pollen types (from NAAF pollenvarsel.naaf.no)
COMMON_POLLEN_TYPES = [
    "or",      # Alder
    "hassel",  # Hazel
    "salix",   # Willow
    "bjork",   # Birch
    "gress",   # Grass
    "burot"    # Mugwort
]

# Mapping from Norwegian names to English names
POLLEN_NAME_MAPPING = {
    "or": "alder",
    "hassel": "hazel", 
    "salix": "willow",
    "bjork": "birch",
    "gress": "grass",
    "burot": "mugwort"
}

# Sensor device classes
DEVICE_CLASS_POLLEN = "pollen"

# Sensor icons (using Norwegian pollen types)
POLLEN_ICONS = {
    "or": "mdi:tree",           # Alder
    "hassel": "mdi:tree",       # Hazel
    "salix": "mdi:tree",        # Willow
    "bjork": "mdi:tree",        # Birch
    "gress": "mdi:grass",       # Grass
    "burot": "mdi:flower",      # Mugwort
    "default": "mdi:flower-pollen"
}

# Sensor state colors for card display
POLLEN_COLORS = {
    0: "#4CAF50",  # Green - None
    1: "#FFEB3B",  # Yellow - Low
    2: "#FF9800",  # Orange - Moderate
    3: "#F44336",  # Red - Heavy
    4: "#9C27B0"   # Purple - Extreme
}