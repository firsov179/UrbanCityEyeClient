"""
Actions related to geographic objects and spatial operations
"""
import asyncio
import json
from ..utils.api_client import APIClient
from ..dispatch.dispatcher import Dispatcher
from ..utils.geo_utils import calculate_distance, parse_geojson


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

        # Prepare query parameters
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

        # Open the info panel when an object is selected
        dispatcher.dispatch("TOGGLE_INFO_PANEL", True)

        # Center map if requested
        if center_map and geo_object:
            try:
                # Parse the geometry and find the center
                geometry = geo_object.get("geometry", {})
                center = GeoActions.get_geometry_center(geometry)

                if center:
                    dispatcher.dispatch("SET_MAP_VIEW", {"center": center})
            except Exception as e:
                js.console.log(f"Error centering map on object: {str(e)}")

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
                # Point is already a center
                return coords

            elif geo_type == "LineString":
                # For a line, use the middle point
                if len(coords) > 0:
                    middle_idx = len(coords) // 2
                    return coords[middle_idx]

            elif geo_type == "Polygon":
                # For a polygon, calculate centroid of the exterior ring
                if len(coords) > 0 and len(coords[0]) > 0:
                    # Simple average of coordinates (approximate centroid)
                    points = coords[0]  # Exterior ring
                    lng_sum = sum(point[0] for point in points)
                    lat_sum = sum(point[1] for point in points)
                    return [lng_sum / len(points), lat_sum / len(points)]

            elif geo_type == "MultiPoint":
                # Average all points
                if len(coords) > 0:
                    lng_sum = sum(point[0] for point in coords)
                    lat_sum = sum(point[1] for point in coords)
                    return [lng_sum / len(coords), lat_sum / len(coords)]

            elif geo_type == "MultiLineString":
                # Use the middle point of the first line
                if len(coords) > 0 and len(coords[0]) > 0:
                    line = coords[0]
                    middle_idx = len(line) // 2
                    return line[middle_idx]

            elif geo_type == "MultiPolygon":
                # Use the centroid of the first polygon
                if len(coords) > 0 and len(coords[0]) > 0 and len(coords[0][0]) > 0:
                    points = coords[0][0]  # First polygon's exterior ring
                    lng_sum = sum(point[0] for point in points)
                    lat_sum = sum(point[1] for point in points)
                    return [lng_sum / len(points), lat_sum / len(points)]

        except Exception as e:
            js.console.log(f"Error calculating geometry center: {str(e)}")

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

        # If simulation_id is not provided, use the current one
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

        # Prepare query parameters
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

        # Get current layers and their visibility
        layers = state.get("map_layers", {})

        # Determine new visibility state
        if layer_id in layers:
            layer = layers[layer_id]
            if visible is None:
                # Toggle current state
                visible = not layer.get("visible", True)
        else:
            # Default to visible if layer doesn't exist yet
            if visible is None:
                visible = True

        # Update the layer
        layers[layer_id] = {
            "id": layer_id,
            "visible": visible
        }

        # Dispatch the update
        dispatcher = Dispatcher()
        dispatcher.dispatch("UPDATE_MAP_LAYERS", layers)

    @staticmethod
    def create_buffer(geo_object, distance_meters):
        """
        Create a buffer around a geographic object
        
        Args:
            geo_object: GeoJSON Feature
            distance_meters: Buffer distance in meters
            
        Returns:
            Buffered GeoJSON Feature or None if operation fails
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("BUFFER_REQUEST")

        # This would typically be a server-side operation with PostGIS
        # For PyScript, we would need a client-side implementation or server API
        # This is a placeholder that would need to be implemented

        # For now, we'll just return a mock result
        buffered_feature = {
            "type": "Feature",
            "geometry": geo_object.get("geometry"),  # This should be the buffered geometry
            "properties": {
                "original_id": geo_object.get("properties", {}).get("id"),
                "buffer_distance": distance_meters,
                "is_buffer": True
            }
        }

        dispatcher.dispatch("SET_BUFFER_RESULT", buffered_feature)
        return buffered_feature

    @staticmethod
    async def find_nearest_features(point, max_distance=1000, limit=5, simulation_id=None):
        """
        Find the nearest features to a point
        
        Args:
            point: [lng, lat] coordinates
            max_distance: Maximum distance in meters
            limit: Maximum number of results
            simulation_id: Optional simulation ID to restrict search
            
        Returns:
            List of nearest features or None if request fails
        """
        from ..store.app_store import AppStore

        store = AppStore()
        state = store.get_state()

        # If simulation_id is not provided, use the current one
        if not simulation_id:
            simulation = state.get("simulation")
            if simulation:
                simulation_id = simulation.get("id")

        if not simulation_id:
            dispatcher = Dispatcher()
            dispatcher.dispatch("API_ERROR", "No simulation ID available for nearest search")
            return None

        dispatcher = Dispatcher()
        dispatcher.dispatch("NEAREST_FEATURES_REQUEST")

        # Prepare query parameters
        params = {
            "lng": point[0],
            "lat": point[1],
            "distance": max_distance,
            "limit": limit
        }

        response = await APIClient.get(f"geo-objects/simulation/{simulation_id}/nearest", params)

        if response:
            dispatcher.dispatch("SET_NEAREST_FEATURES", response)
            return response
        else:
            dispatcher.dispatch("API_ERROR", f"Failed to find nearest features")
            return None

    @staticmethod
    def analyze_geo_data(geo_objects):
        """
        Perform analysis on geographic data
        
        Args:
            geo_objects: GeoJSON FeatureCollection to analyze
            
        Returns:
            Analysis results dictionary
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("GEO_ANALYSIS_REQUEST")

        # Parse the GeoJSON
        features = parse_geojson(geo_objects)

        if not features:
            dispatcher.dispatch("API_ERROR", "Invalid GeoJSON for analysis")
            return None

        # Count objects by type
        type_counts = {}
        for feature in features:
            props = feature.get("properties", {})
            role = props.get("role", "unknown")

            # Extract the main type from the role
            role_parts = role.split(":")
            main_type = role_parts[0] if len(role_parts) > 0 else role

            # Count by main type
            if main_type in type_counts:
                type_counts[main_type] += 1
            else:
                type_counts[main_type] = 1

        # Calculate total length of linear features
        total_length = 0
        for feature in features:
            geometry = feature.get("geometry", {})
            if geometry.get("type") == "LineString":
                coords = geometry.get("coordinates", [])
                length = 0

                # Calculate length by summing distances between consecutive points
                for i in range(1, len(coords)):
                    point1 = coords[i - 1]
                    point2 = coords[i]
                    segment_length = calculate_distance(point1, point2)
                    length += segment_length

                total_length += length

        # Prepare analysis results
        analysis = {
            "total_objects": len(features),
            "type_distribution": type_counts,
            "total_length_km": round(total_length, 2),
        }

        dispatcher.dispatch("SET_GEO_ANALYSIS", analysis)
        return analysis

    @staticmethod
    def export_geo_data(geo_objects, format="geojson"):
        """
        Export geographic data to different formats
        
        Args:
            geo_objects: GeoJSON FeatureCollection to export
            format: Export format ("geojson", "csv", etc.)
            
        Returns:
            Data in the requested format or None if export fails
        """
        try:
            if format == "geojson":
                # Already in GeoJSON format, just stringify
                return json.dumps(geo_objects, indent=2)

            elif format == "csv":
                # Convert to CSV format
                csv_rows = ["id,name,role,latitude,longitude"]

                for feature in geo_objects.get("features", []):
                    props = feature.get("properties", {})
                    geometry = feature.get("geometry", {})

                    # Extract center point
                    center = GeoActions.get_geometry_center(geometry)

                    if center and props:
                        row = [
                            str(props.get("id", "")),
                            props.get("name", "").replace(",", ";"),  # Escape commas
                            props.get("role", "").replace(",", ";"),  # Escape commas
                            str(center[1]),  # latitude
                            str(center[0])  # longitude
                        ]
                        csv_rows.append(",".join(row))

                return "\n".join(csv_rows)

            else:
                js.console.log(f"Unsupported export format: {format}")
                return None

        except Exception as e:
            js.console.log(f"Error exporting geo data: {str(e)}")
            return None
