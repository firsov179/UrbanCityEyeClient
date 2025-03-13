"""
Utilities module for client application.
Provides helper functions and classes for various operations.
"""

from .api_client import APIClient
from .geo_utils import (
    calculate_distance,
    format_coordinates,
    create_geojson_layer,
    parse_geojson
)
from logging import log, error, warn

# Exports
__all__ = [
    'APIClient',
    'calculate_distance',
    'format_coordinates',
    'create_geojson_layer',
    'parse_geojson',
    'log',
    'error',
    'warn'
]

