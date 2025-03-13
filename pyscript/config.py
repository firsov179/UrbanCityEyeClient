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

# City Positions (for home screen map)
CITY_POSITIONS = {
    "London": {"left": 23.3, "top": 54},
    "Paris": {"left": 28, "top": 65},
    "Moscow": {"left": 66, "top": 44},
    "Rome": {"left": 40, "top": 83},
    "Saint Petersburg": {"left": 59, "top": 35}
}
