"""
Application configuration settings
"""

# API Configuration
API_BASE_URL = "http://urbancityeye.ru:7007/api"
API_TIMEOUT = 10

# Map Configuration
MAP_DEFAULT_CENTER = [51.5074, -0.1278]
MAP_DEFAULT_ZOOM = 13
MAP_TILE_LAYER = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
MAP_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'

# City Positions
CITY_POSITIONS = {
    1: {"left": 23.3, "top": 54},
    2: {"left": 28, "top": 65},
    3: {"left": 66, "top": 44},
    4: {"left": 40, "top": 83},
    5: {"left": 59, "top": 35}
}
