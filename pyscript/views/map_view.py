"""
Map view component for displaying geographic data using Leaflet
"""
import js
import json
from pyodide.ffi import create_proxy
from ..store.app_store import AppStore
from ..actions.geo_actions import GeoActions
from ..config import MAP_DEFAULT_CENTER, MAP_DEFAULT_ZOOM, MAP_TILE_LAYER, MAP_ATTRIBUTION


class MapView:
    """Map view component for displaying geographic data"""

    def __init__(self, container_id="map-container"):
        """
        Initialize the map view
        
        Args:
            container_id: ID of the HTML container element
        """
        self.container_id = container_id
        self.container = js.document.getElementById(container_id)
        self.store = AppStore()
        self.unsubscribe = None
        self.map = None
        self.layers = {}
        self.popup = None
        self.selected_layer = None

    def initialize(self):
        """Initialize the component, create the map and subscribe to store updates"""
        if self.container is None:
            print(f"Warning: Container {self.container_id} not found in the DOM")
            return

        # Initialize the Leaflet map
        self.create_map()

        # Subscribe to store changes
        self.unsubscribe = self.store.subscribe(create_proxy(self.on_state_change))

    def create_map(self):
        """Create the Leaflet map instance"""
        try:
            # Check if the container exists
            if not self.container:
                print(f"Error: Map container '{self.container_id}' not found in DOM")
                return

            # Check if the container already has a map
            if hasattr(self, 'map') and self.map:
                print("Removing existing map instance")
                self.map.remove()
                self.map = None

            # Clear any previous content
            if self.container.childElementCount > 0:
                self.container.innerHTML = ""

            # Validate and fix center coordinates
            from ..config import MAP_DEFAULT_CENTER, MAP_DEFAULT_ZOOM

            # Debug: log the values
            print(f"MAP_DEFAULT_CENTER: {MAP_DEFAULT_CENTER}, type: {type(MAP_DEFAULT_CENTER)}")

            # Default center for London if coordinates are invalid
            center = [51.5074, -0.1278]  # [lat, lng] - London coordinates

            # Check if MAP_DEFAULT_CENTER is valid
            if MAP_DEFAULT_CENTER and isinstance(MAP_DEFAULT_CENTER, list) and len(MAP_DEFAULT_CENTER) == 2:
                # Verify each coordinate is a number
                if all(isinstance(coord, (int, float)) for coord in MAP_DEFAULT_CENTER):
                    center = MAP_DEFAULT_CENTER
                    print(f"Using config center: {center}")
                else:
                    print(f"Invalid coordinates in MAP_DEFAULT_CENTER: {MAP_DEFAULT_CENTER}")
            else:
                print(f"Invalid MAP_DEFAULT_CENTER format: {MAP_DEFAULT_CENTER}")

            # Ensure zoom is valid
            zoom = 13  # Default zoom
            if isinstance(MAP_DEFAULT_ZOOM, int):
                zoom = MAP_DEFAULT_ZOOM

            print(f"Creating map with center: {center}, zoom: {zoom}")

            # Create a map with the validated center and zoom
            # Ensure the order is [lat, lng]
            self.map = js.L.map(self.container_id).setView([center[0], center[1]], zoom)

            # Add tile layer
            from ..config import MAP_TILE_LAYER, MAP_ATTRIBUTION

            # Use default values if config values are not available
            tile_layer = MAP_TILE_LAYER if MAP_TILE_LAYER else 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
            attribution = MAP_ATTRIBUTION if MAP_ATTRIBUTION else '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'

            js.L.tileLayer(tile_layer, {
                "attribution": attribution,
                "maxZoom": 19
            }).addTo(self.map)

            # Add event handlers
            from pyodide.ffi import create_proxy
            self.map.on("click", create_proxy(self.on_map_click))
            self.map.on("zoomend", create_proxy(self.on_map_zoom))
            self.map.on("moveend", create_proxy(self.on_map_move))

            print("Map created successfully")

        except Exception as e:
            import traceback
            print(f"Error creating map: {str(e)}")
            print(traceback.format_exc())

    def on_state_change(self, state):
        """
        Handle state changes from the store
        
        Args:
            state: Current application state
        """
        # Check for new geo objects
        geo_objects = state.get("geo_objects")

        if geo_objects:
            self.update_geo_layers(geo_objects)

        # Check for selected object
        selected_object = state.get("selected_object")

        if selected_object:
            self.highlight_selected_object(selected_object)
        else:
            self.clear_selection()

        # Check for map view changes
        map_center = state.get("map_center")
        map_zoom = state.get("map_zoom")

        if map_center and self.map:
            self.map.setView(map_center, map_zoom if map_zoom else self.map.getZoom())

    def update_geo_layers(self, geo_objects):
        """
        Update map layers with new geographic objects
        
        Args:
            geo_objects: GeoJSON FeatureCollection
        """
        # Clear existing layers
        if 'main' in self.layers:
            self.map.removeLayer(self.layers['main'])

        # Parse the GeoJSON if it's a string
        if isinstance(geo_objects, str):
            try:
                geo_objects = json.loads(geo_objects)
            except Exception as e:
                print(f"Error parsing GeoJSON: {str(e)}")
                return

        # Create the GeoJSON layer
        try:
            # Style function for GeoJSON features
            style_function = """
            function(feature) {
                let role = feature.properties.role || '';
                
                // Default style
                let style = {
                    weight: 2,
                    opacity: 0.7,
                    color: '#3388ff',
                    fillOpacity: 0.2
                };
                
                // Style based on feature role
                if (role.includes('highway')) {
                    style.color = '#FF5733';
                    style.weight = 3;
                } else if (role.includes('railway')) {
                    style.color = '#581845';
                    style.weight = 2;
                    style.dashArray = '4,4';
                } else if (role.includes('waterway')) {
                    style.color = '#3D85C6';
                    style.weight = 2;
                } else if (role.includes('building')) {
                    style.color = '#666666';
                    style.fillOpacity = 0.4;
                    style.weight = 1;
                }
                
                return style;
            }
            """

            # Point to layer function for markers
            point_to_layer = """
            function(feature, latlng) {
                let role = feature.properties.role || '';
                let marker;
                
                if (role.includes('amenity')) {
                    marker = L.circleMarker(latlng, {
                        radius: 6,
                        fillColor: '#FF9900',
                        color: '#000',
                        weight: 1,
                        opacity: 1,
                        fillOpacity: 0.8
                    });
                } else {
                    marker = L.circleMarker(latlng, {
                        radius: 4,
                        fillColor: '#3388ff',
                        color: '#fff',
                        weight: 1,
                        opacity: 1,
                        fillOpacity: 0.8
                    });
                }
                
                return marker;
            }
            """

            # On each feature function for adding popups and events
            on_each_feature = """
            function(feature, layer) {
                if (feature.properties && feature.properties.name) {
                    layer.bindTooltip(feature.properties.name);
                }
                
                layer.on('click', function(e) {
                    window.pyodide.runPython(`
                        from js import event
                        from pyscript.views.map_view import MapView
                        MapView.on_feature_click(event, ${JSON.stringify(feature)})
                    `);
                    
                    // Stop click event from propagating to the map
                    L.DomEvent.stopPropagation(e);
                });
            }
            """

            # Create the GeoJSON layer with our custom functions
            layer = js.L.geoJSON(geo_objects, {
                "style": js.eval(style_function),
                "pointToLayer": js.eval(point_to_layer),
                "onEachFeature": js.eval(on_each_feature)
            })

            # Add the layer to the map
            layer.addTo(self.map)

            # Store the layer
            self.layers['main'] = layer

            # Fit the map to the layer bounds
            bounds = layer.getBounds()
            if bounds.isValid():
                self.map.fitBounds(bounds)

        except Exception as e:
            print(f"Error creating GeoJSON layer: {str(e)}")

    def highlight_selected_object(self, selected_object):
        """
        Highlight the selected object on the map
        
        Args:
            selected_object: GeoJSON Feature to highlight
        """
        # Clear previous selection
        self.clear_selection()

        try:
            # Parse the object if it's a string
            if isinstance(selected_object, str):
                selected_object = json.loads(selected_object)

            # Create a highlighted style
            highlight_style = {
                "color": "#ff0000",
                "weight": 4,
                "opacity": 1,
                "fillColor": "#ff0000",
                "fillOpacity": 0.3
            }

            # Create a new layer for the selected object
            self.selected_layer = js.L.geoJSON(selected_object, {"style": highlight_style})

            # Add the layer to the map and bring to front
            self.selected_layer.addTo(self.map)
            self.selected_layer.bringToFront()

            # Center the map on the selected object
            bounds = self.selected_layer.getBounds()
            if bounds.isValid():
                self.map.fitBounds(bounds, {"padding": [50, 50]})

        except Exception as e:
            print(f"Error highlighting selected object: {str(e)}")

    def clear_selection(self):
        """Clear the currently selected object"""
        if self.selected_layer:
            self.map.removeLayer(self.selected_layer)
            self.selected_layer = None

    def on_map_click(self, event):
        """
        Handle map click event
        
        Args:
            event: Leaflet click event
        """
        # Close popup if open
        if self.popup:
            self.map.closePopup(self.popup)
            self.popup = None

        # Clear selected object
        self.store.update_state({"selected_object": None})

    @staticmethod
    def on_feature_click(event, feature):
        """
        Handle feature click event (static method called from JavaScript)
        
        Args:
            event: Leaflet click event
            feature: GeoJSON Feature
        """
        # Select the clicked object
        GeoActions.select_geo_object(feature)

    def on_map_zoom(self, event):
        """
        Handle map zoom event
        
        Args:
            event: Leaflet zoom event
        """
        # Update map zoom in the store
        GeoActions.update_map_view(
            self.map.getCenter(),
            self.map.getZoom()
        )

    def on_map_move(self, event):
        """
        Handle map move event
        
        Args:
            event: Leaflet move event
        """
        # Update map center in the store
        GeoActions.update_map_view(
            self.map.getCenter(),
            self.map.getZoom()
        )

    def cleanup(self):
        """Clean up the component and unsubscribe from the store"""
        if self.unsubscribe:
            self.unsubscribe()

        # Clean up the map
        if self.map:
            self.map.remove()
            self.map = None
