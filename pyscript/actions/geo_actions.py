"""
Actions related to geographic objects and spatial operations
"""
import asyncio
import json
from ..utils.api_client import APIClient
from ..dispatch.dispatcher import Dispatcher
from ..utils.geo_utils import calculate_distance, parse_geojson
from ..utils.logging import *

class GeoActions:
    """Actions for managing geographic objects and spatial operations"""

    @staticmethod
    async def fetch_geo_object(geo_object_id):
        """
        Fetch a specific geographic object by ID
        
        Args:
            geo_object_id: ID of the geographic object
            
        Returns:
            GeoJSON Feature or None if the request fails
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("GEO_OBJECT_REQUEST")

        response = await APIClient.get(f"geo-objects/{geo_object_id}")

        if response:
            dispatcher.dispatch("SET_SELECTED_GEO_OBJECT", response)
            return response
        else:
            dispatcher.dispatch("API_ERROR", f"Failed to fetch geo object {geo_object_id}")
            return None

    @staticmethod
    async def search_geo_objects(query, simulation_id=None):
        """
        Search for geographic objects by name or attributes
        
        Args:
            query: Search query string
            simulation_id: Optional simulation ID to restrict search
            
        Returns:
            List of matching objects or None if the request fails
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("GEO_SEARCH_REQUEST")

        params = {"q": query}
        if simulation_id:
            params["simulation_id"] = simulation_id

        response = await APIClient.get("geo-objects/search", params)

        if response:
            dispatcher.dispatch("SET_SEARCH_RESULTS", response)
            return response
        else:
            dispatcher.dispatch("API_ERROR", f"Failed to search for geo objects: {query}")
            return None

    @staticmethod
    def select_geo_object(geo_object, center_map=True):
        """
        Select a geographic object and optionally center the map on it
        
        Args:
            geo_object: GeoJSON Feature to select
            center_map: Whether to center the map on the object
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("SELECT_GEO_OBJECT", geo_object)

        dispatcher.dispatch("TOGGLE_INFO_PANEL", True)

        if center_map and geo_object:
            try:
                geometry = geo_object.get("geometry", {})
                center = GeoActions.get_geometry_center(geometry)

                if center:
                    dispatcher.dispatch("SET_MAP_VIEW", {"center": center})
            except Exception as e:
                error(f"Error centering map on object: {str(e)}")

    @staticmethod
    def get_geometry_center(geometry):
        """
        Calculate the center point of a GeoJSON geometry
        
        Args:
            geometry: GeoJSON geometry object
            
        Returns:
            [lng, lat] coordinates of the center or None if calculation fails
        """
        if not geometry or "type" not in geometry:
            return None

        geo_type = geometry.get("type")
        coords = geometry.get("coordinates", [])

        try:
            if geo_type == "Point":
                return coords

            elif geo_type == "LineString":
                if len(coords) > 0:
                    middle_idx = len(coords) // 2
                    return coords[middle_idx]

            elif geo_type == "Polygon":
                if len(coords) > 0 and len(coords[0]) > 0:
                    points = coords[0]
                    lng_sum = sum(point[0] for point in points)
                    lat_sum = sum(point[1] for point in points)
                    return [lng_sum / len(points), lat_sum / len(points)]

            elif geo_type == "MultiPoint":
                if len(coords) > 0:
                    lng_sum = sum(point[0] for point in coords)
                    lat_sum = sum(point[1] for point in coords)
                    return [lng_sum / len(coords), lat_sum / len(coords)]

            elif geo_type == "MultiLineString":
                if len(coords) > 0 and len(coords[0]) > 0:
                    line = coords[0]
                    middle_idx = len(line) // 2
                    return line[middle_idx]

            elif geo_type == "MultiPolygon":
                if len(coords) > 0 and len(coords[0]) > 0 and len(coords[0][0]) > 0:
                    points = coords[0][0]
                    lng_sum = sum(point[0] for point in points)
                    lat_sum = sum(point[1] for point in points)
                    return [lng_sum / len(points), lat_sum / len(points)]

        except Exception as e:
            error(f"Error calculating geometry center: {str(e)}")

        return None

    @staticmethod
    async def filter_geo_objects_by_type(types, simulation_id=None):
        """
        Filter geographic objects by their type/role
        
        Args:
            types: List of types to filter by (e.g., ["highway:residential", "railway"])
            simulation_id: Optional simulation ID to restrict filtering
            
        Returns:
            Filtered GeoJSON data or None if request fails
        """
        from ..store.app_store import AppStore

        store = AppStore()
        state = store.get_state()

        if not simulation_id:
            simulation = state.get("simulation")
            if simulation:
                simulation_id = simulation.get("id")

        if not simulation_id:
            dispatcher = Dispatcher()
            dispatcher.dispatch("API_ERROR", "No simulation ID available for filtering")
            return None

        dispatcher = Dispatcher()
        dispatcher.dispatch("GEO_FILTER_REQUEST")

        params = {"types": ",".join(types)}

        response = await APIClient.get(f"geo-objects/simulation/{simulation_id}/filter", params)

        if response:
            dispatcher.dispatch("SET_FILTERED_GEO_OBJECTS", response)
            return response
        else:
            dispatcher.dispatch("API_ERROR", f"Failed to filter geo objects for simulation {simulation_id}")
            return None

    @staticmethod
    def toggle_geo_layer(layer_id, visible=None):
        """
        Toggle visibility of a geographic layer
        
        Args:
            layer_id: ID of the layer to toggle
            visible: Optional explicit visibility state (True=visible, False=hidden)
                     If None, toggles the current state
        """
        from ..store.app_store import AppStore

        store = AppStore()
        state = store.get_state()

        layers = state.get("map_layers", {})

        if layer_id in layers:
            layer = layers[layer_id]
            if visible is None:
                visible = not layer.get("visible", True)
        else:
            if visible is None:
                visible = True

        layers[layer_id] = {
            "id": layer_id,
            "visible": visible
        }

        dispatcher = Dispatcher()
        dispatcher.dispatch("UPDATE_MAP_LAYERS", layers)
