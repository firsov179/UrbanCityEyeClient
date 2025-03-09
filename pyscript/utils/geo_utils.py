"""
Geo utilities module for working with geographic data
Contains functions for calculations, transformations, and visualization of geographic data
"""
import math
import json
from typing import List, Dict, Tuple, Union, Any

def calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    Calculate the Haversine distance between two points in kilometers
    
    Args:
        point1: (longitude, latitude) coordinates of first point
        point2: (longitude, latitude) coordinates of second point
        
    Returns:
        Distance in kilometers
    """
    # Earth radius in kilometers
    R = 6371.0
    
    # Convert coordinates from degrees to radians
    lon1, lat1 = map(math.radians, point1)
    lon2, lat2 = map(math.radians, point2)
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distance = R * c
    return distance

def format_coordinates(coords: Tuple[float, float], format_type: str = "dms") -> str:
    """
    Format coordinates in different formats
    
    Args:
        coords: (longitude, latitude) coordinates
        format_type: Format type: "dms" (degrees, minutes, seconds), 
                     "dm" (degrees, minutes), or "dd" (decimal degrees)
    
    Returns:
        Formatted coordinates string
    """
    lon, lat = coords
    
    if format_type == "dd":
        # Decimal degrees format
        return f"{lat:.6f}°N, {lon:.6f}°E"
    
    elif format_type == "dm":
        # Degrees and decimal minutes format
        lat_deg = int(abs(lat))
        lat_min = (abs(lat) - lat_deg) * 60
        lat_dir = "N" if lat >= 0 else "S"
        
        lon_deg = int(abs(lon))
        lon_min = (abs(lon) - lon_deg) * 60
        lon_dir = "E" if lon >= 0 else "W"
        
        return f"{lat_deg}° {lat_min:.3f}' {lat_dir}, {lon_deg}° {lon_min:.3f}' {lon_dir}"
    
    else:  # format_type == "dms"
        # Degrees, minutes, seconds format
        lat_deg = int(abs(lat))
        lat_min = int((abs(lat) - lat_deg) * 60)
        lat_sec = ((abs(lat) - lat_deg) * 60 - lat_min) * 60
        lat_dir = "N" if lat >= 0 else "S"
        
        lon_deg = int(abs(lon))
        lon_min = int((abs(lon) - lon_deg) * 60)
        lon_sec = ((abs(lon) - lon_deg) * 60 - lon_min) * 60
        lon_dir = "E" if lon >= 0 else "W"
        
        return f"{lat_deg}° {lat_min}' {lat_sec:.2f}\" {lat_dir}, {lon_deg}° {lon_min}' {lon_sec:.2f}\" {lon_dir}"

def create_geojson_layer(geojson_data: Union[Dict, str], style: Dict = None) -> Dict:
    """
    Prepare GeoJSON for use with Leaflet
    
    Args:
        geojson_data: GeoJSON data as dictionary or string
        style: Optional style to apply to the GeoJSON
    
    Returns:
        Dictionary with layer configuration
    """
    # Parse GeoJSON if it's a string
    if isinstance(geojson_data, str):
        try:
            geojson_data = json.loads(geojson_data)
        except json.JSONDecodeError:
            raise ValueError("Invalid GeoJSON string")
    
    # Default style if none provided
    if style is None:
        style = {
            "weight": 2,
            "opacity": 0.7,
            "color": "#3388ff",
            "fillOpacity": 0.2
        }
    
    return {
        "data": geojson_data,
        "style": style
    }

def parse_geojson(geojson_data: Union[Dict, str]) -> List[Dict]:
    """
    Parse GeoJSON data and extract features
    
    Args:
        geojson_data: GeoJSON data as dictionary or string
    
    Returns:
        List of GeoJSON features
    """
    # Parse GeoJSON if it's a string
    if isinstance(geojson_data, str):
        try:
            geojson_data = json.loads(geojson_data)
        except json.JSONDecodeError:
            raise ValueError("Invalid GeoJSON string")
    
    # Handle FeatureCollection
    if geojson_data.get("type") == "FeatureCollection":
        return geojson_data.get("features", [])
    
    # Handle single Feature
    elif geojson_data.get("type") == "Feature":
        return [geojson_data]
    
    # Handle Geometry (create a feature with it)
    elif geojson_data.get("type") in ["Point", "LineString", "Polygon", 
                                     "MultiPoint", "MultiLineString", 
                                     "MultiPolygon", "GeometryCollection"]:
        return [{
            "type": "Feature",
            "geometry": geojson_data,
            "properties": {}
        }]
    
    # Unknown type
    return []

def get_geometry_center(geometry: Dict) -> Tuple[float, float]:
    """
    Calculate the center point of a GeoJSON geometry
    
    Args:
        geometry: GeoJSON geometry object
    
    Returns:
        (longitude, latitude) coordinates of the center
    """
    if not geometry or "type" not in geometry:
        raise ValueError("Invalid geometry object")
    
    geo_type = geometry.get("type")
    coords = geometry.get("coordinates", [])
    
    if geo_type == "Point":
        # Point is already a center
        return tuple(coords)
    
    elif geo_type == "LineString":
        # For a line, use the middle point
        if len(coords) > 0:
            middle_idx = len(coords) // 2
            return tuple(coords[middle_idx])
    
    elif geo_type == "Polygon":
        # For a polygon, calculate centroid of the exterior ring
        if len(coords) > 0 and len(coords[0]) > 0:
            # Simple average of coordinates (approximate centroid)
            points = coords[0]  # Exterior ring
            lng_sum = sum(point[0] for point in points)
            lat_sum = sum(point[1] for point in points)
            return (lng_sum / len(points), lat_sum / len(points))
    
    elif geo_type == "MultiPoint":
        # Average all points
        if len(coords) > 0:
            lng_sum = sum(point[0] for point in coords)
            lat_sum = sum(point[1] for point in coords)
            return (lng_sum / len(coords), lat_sum / len(coords))
    
    elif geo_type == "MultiLineString":
        # Use the middle point of the first line
        if len(coords) > 0 and len(coords[0]) > 0:
            line = coords[0]
            middle_idx = len(line) // 2
            return tuple(line[middle_idx])
    
    elif geo_type == "MultiPolygon":
        # Use the centroid of the first polygon
        if len(coords) > 0 and len(coords[0]) > 0 and len(coords[0][0]) > 0:
            points = coords[0][0]  # First polygon's exterior ring
            lng_sum = sum(point[0] for point in points)
            lat_sum = sum(point[1] for point in points)
            return (lng_sum / len(points), lat_sum / len(points))
    
    # Default center (0,0) if calculation fails
    return (0.0, 0.0)

def calculate_bbox(geojson_data: Union[Dict, str]) -> List[float]:
    """
    Calculate the bounding box of GeoJSON data
    
    Args:
        geojson_data: GeoJSON data as dictionary or string
    
    Returns:
        Bounding box as [minX, minY, maxX, maxY]
    """
    features = parse_geojson(geojson_data)
    
    if not features:
        return [0, 0, 0, 0]
    
    # Initialize with extreme values
    min_x = float('inf')
    min_y = float('inf')
    max_x = float('-inf')
    max_y = float('-inf')
    
    def update_bounds(coords):
        nonlocal min_x, min_y, max_x, max_y
        
        # Handle different coordinate structures
        if isinstance(coords[0], (int, float)):
            # It's a single point
            x, y = coords
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
        else:
            # It's an array of coordinates (recursive)
            for coord in coords:
                update_bounds(coord)
    
    # Process each feature
    for feature in features:
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates", [])
        
        # Update bounds with this geometry's coordinates
        update_bounds(coords)
    
    # Return the bounding box
    return [min_x, min_y, max_x, max_y]

def transform_crs(coords: Tuple[float, float], from_crs: str, to_crs: str) -> Tuple[float, float]:
    """
    Transform coordinates between different coordinate reference systems
    
    NOTE: This is a simplified implementation. In a real-world application,
    you would use a library like PyProj or make API calls to a transformation service.
    
    Args:
        coords: (x, y) or (longitude, latitude) coordinates
        from_crs: Source CRS identifier (e.g., "EPSG:4326" for WGS84)
        to_crs: Target CRS identifier (e.g., "EPSG:3857" for Web Mercator)
    
    Returns:
        Transformed coordinates as (x, y)
    """
    x, y = coords
    
    # Simple transformation from WGS84 (EPSG:4326) to Web Mercator (EPSG:3857)
    if from_crs == "EPSG:4326" and to_crs == "EPSG:3857":
        # Convert longitude/latitude to Web Mercator
        if abs(y) > 85.06:
            # Clamp to valid range
            y = 85.06 if y > 0 else -85.06
            
        earth_radius = 6378137.0  # Earth radius in meters
        
        # Transform longitude
        mercator_x = x * math.pi * earth_radius / 180.0
        
        # Transform latitude
        mercator_y = math.log(math.tan((90.0 + y) * math.pi / 360.0)) * earth_radius
        
        return (mercator_x, mercator_y)
    
    # Simple transformation from Web Mercator (EPSG:3857) to WGS84 (EPSG:4326)
    elif from_crs == "EPSG:3857" and to_crs == "EPSG:4326":
        earth_radius = 6378137.0  # Earth radius in meters
        
        # Transform x to longitude
        longitude = x * 180.0 / (math.pi * earth_radius)
        
        # Transform y to latitude
        latitude = 360.0 * math.atan(math.exp(y / earth_radius)) / math.pi - 90.0
        
        return (longitude, latitude)
    
    # For other transformations, we would need a more complete library
    # For now, just return the original coordinates
    return coords

def simplify_geometry(geometry: Dict, tolerance: float = 0.00001) -> Dict:
    """
    Simplify a GeoJSON geometry using the Ramer-Douglas-Peucker algorithm
    
    Args:
        geometry: GeoJSON geometry object
        tolerance: Simplification tolerance (distance threshold)
        
    Returns:
        Simplified GeoJSON geometry
    """
    def point_line_distance(point, line_start, line_end):
        """Calculate the perpendicular distance from a point to a line"""
        if line_start == line_end:
            return math.sqrt((point[0] - line_start[0])**2 + (point[1] - line_start[1])**2)
        
        n = abs((line_end[1] - line_start[1]) * point[0] - 
                (line_end[0] - line_start[0]) * point[1] + 
                line_end[0] * line_start[1] - 
                line_end[1] * line_start[0])
        
        d = math.sqrt((line_end[1] - line_start[1])**2 + (line_end[0] - line_start[0])**2)
        
        return n / d
    
    def simplify_points(points, tolerance):
        """Simplify a list of points using Douglas-Peucker algorithm"""
        if len(points) <= 2:
            return points
        
        # Find the point with the maximum distance
        dmax = 0
        index = 0
        start = points[0]
        end = points[-1]
        
        for i in range(1, len(points) - 1):
            d = point_line_distance(points[i], start, end)
            if d > dmax:
                index = i
                dmax = d
        
        # If max distance is greater than tolerance, recursively simplify
        if dmax > tolerance:
            # Recursive call
            first_segment = simplify_points(points[:index + 1], tolerance)
            second_segment = simplify_points(points[index:], tolerance)
            
            # Build the result list (avoiding duplicating the connection point)
            return first_segment[:-1] + second_segment
        else:
            return [points[0], points[-1]]
    
    # Clone the geometry to avoid modifying the original
    result = dict(geometry)
    
    if not geometry or "type" not in geometry or "coordinates" not in geometry:
        return result
    
    geo_type = geometry["type"]
    
    if geo_type == "Point" or geo_type == "MultiPoint":
        # Points can't be simplified
        return result
    
    elif geo_type == "LineString":
        result["coordinates"] = simplify_points(geometry["coordinates"], tolerance)
    
    elif geo_type == "Polygon":
        # Simplify each ring (keeping first and last points the same)
        rings = []
        for ring in geometry["coordinates"]:
            if len(ring) <= 4:  # A triangle plus closing point - can't simplify further
                rings.append(ring)
            else:
                # For rings, first and last points must be the same
                simplified_ring = simplify_points(ring[:-1], tolerance)
                # Make sure we have at least 3 points (a triangle)
                if len(simplified_ring) < 3:
                    rings.append(ring)
                else:
                    # Close the ring by adding the first point at the end
                    simplified_ring.append(simplified_ring[0])
                    rings.append(simplified_ring)
        
        result["coordinates"] = rings
    
    elif geo_type == "MultiLineString":
        result["coordinates"] = [
            simplify_points(line, tolerance) for line in geometry["coordinates"]
        ]
    
    elif geo_type == "MultiPolygon":
        multi_polygon = []
        for polygon in geometry["coordinates"]:
            rings = []
            for ring in polygon:
                if len(ring) <= 4:  # Can't simplify further
                    rings.append(ring)
                else:
                    # For rings, first and last points must be the same
                    simplified_ring = simplify_points(ring[:-1], tolerance)
                    # Make sure we have at least 3 points
                    if len(simplified_ring) < 3:
                        rings.append(ring)
                    else:
                        # Close the ring
                        simplified_ring.append(simplified_ring[0])
                        rings.append(simplified_ring)
            multi_polygon.append(rings)
        
        result["coordinates"] = multi_polygon
    
    elif geo_type == "GeometryCollection" and "geometries" in geometry:
        # Simplify each geometry in the collection
        result["geometries"] = [
            simplify_geometry(geom, tolerance) for geom in geometry["geometries"]
        ]
    
    return result

