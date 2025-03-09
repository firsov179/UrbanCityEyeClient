"""
Application configuration settings
"""

# API Configuration
API_BASE_URL = "http://127.0.0.1:7007/api"
API_TIMEOUT = 10  # seconds

# Map Configuration
MAP_DEFAULT_CENTER = [51.5074, -0.1278]  # London
MAP_DEFAULT_ZOOM = 13
MAP_TILE_LAYER = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
MAP_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'

# UI Configuration
DEFAULT_CITY_ID = 1  # London
DEFAULT_YEAR = 2000
MAX_INFO_PANEL_ITEMS = 10
TIMELINE_STEP = 5  # Years between timeline markers

