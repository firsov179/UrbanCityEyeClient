"""
Map view component for displaying geographic data using Leaflet
"""
import js
import json
from pyodide.ffi import create_proxy
from ..store.app_store import AppStore
from ..actions.geo_actions import GeoActions
from ..actions.city_actions import CityActions
from ..config import MAP_DEFAULT_CENTER, MAP_DEFAULT_ZOOM
from ..utils.logging import *


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
        self._proxy_handlers = {}
        self._updating_map = False

    def initialize(self):
        """Initialize the component, create the map and subscribe to store updates"""
        if self.container is None:
            warn(f"Warning: Container {self.container_id} not found in the DOM")
            return

        self.create_map()

        self._state_change_handler = create_proxy(self.on_state_change)
        self.unsubscribe = self.store.subscribe(self._state_change_handler)

    def _clear_event_handlers(self):
        """Clear all event handlers and destroy proxies"""
        if not self.map:
            return

        for event_name, handler in self._proxy_handlers.items():
            try:
                self.map.off(event_name, handler)
                handler.destroy()
            except Exception as e:
                error(f"Error removing {event_name} handler: {e}")

        if hasattr(self, 'style_function_proxy') and self.style_function_proxy:
            try:
                self.style_function_proxy.destroy()
                self.style_function_proxy = None
            except Exception as e:
                error(f"Error destroying style function proxy: {e}")

        self._proxy_handlers = {}

    def _setup_event_handlers(self):
        """Set up event handlers for the map with proper proxy management"""

        self._proxy_handlers['click'] = create_proxy(self.on_map_click)
        self._proxy_handlers['zoomend'] = create_proxy(self.on_map_zoom)
        self._proxy_handlers['moveend'] = create_proxy(self.on_map_move)

        self.map.on("click", self._proxy_handlers['click'])
        self.map.on("zoomend", self._proxy_handlers['zoomend'])
        self.map.on("moveend", self._proxy_handlers['moveend'])

    def create_map(self):
        """Create the Leaflet map instance"""
        try:
            if not self.container:
                error(f"Error: Map container '{self.container_id}' not found in DOM")
                return

            if self.map:
                log("Removing existing map instance")
                self._clear_event_handlers()
                try:
                    self.map.remove()
                except Exception as e:
                    error(f"Error removing old map: {e}")
                self.map = None

            if not MAP_DEFAULT_CENTER or len(MAP_DEFAULT_CENTER) != 2:
                center = [51.5074, -0.1278]
                log(f"Using default center: {center}")
            else:
                center = MAP_DEFAULT_CENTER
                log(f"Using configured center: {center}")

            center_obj = js.L.latLng(center[0], center[1])

            zoom = MAP_DEFAULT_ZOOM if isinstance(MAP_DEFAULT_ZOOM, int) else 13

            log(f"Creating map with center: {center}, zoom: {zoom}")
            self.map = js.L.map(self.container_id).setView(center_obj, zoom)

            js.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                "attribution": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                "maxZoom": 19
            }).addTo(self.map)

            js.eval("""
            (function() {
                var style = document.createElement('style');
                style.textContent = '.leaflet-attribution-flag { display: none !important; }';
                document.head.appendChild(style);
            })();
            """)

            self._setup_event_handlers()

            log("Map created successfully")

        except Exception as e:
            import traceback
            error(f"Error creating map: {str(e)}")
            log(traceback.format_exc())

    def cleanup(self):
        """Clean up resources when the component is destroyed"""
        log("Cleaning up MapView resources")

        if self.unsubscribe:
            try:
                self.unsubscribe()
                self.unsubscribe = None
            except Exception as e:
                error(f"Error during unsubscribe: {e}")

        if hasattr(self, '_state_change_handler'):
            try:
                self._state_change_handler.destroy()
            except Exception as e:
                error(f"Error destroying state change handler: {e}")

        self._clear_event_handlers()

        if self.map:
            try:
                self.map.remove()
                self.map = None
            except Exception as e:
                error(f"Error removing map: {e}")

    def on_state_change(self, state):
        """
        Обработка изменений состояния хранилища

        Args:
            state: Текущее состояние приложения
        """
        if self._updating_map:
            log("Skipping state update while map is being programmatically updated")
            return

        geo_objects = state.get("geo_objects")

        if geo_objects and self.map:

            log(f"load {len(geo_objects)} geo_objects")
            current_zoom = self.map.getZoom()

            self._updating_map = True
            try:
                self.update_geo_layers(geo_objects.get('data', geo_objects), preserve_zoom=True)
            finally:
                self._updating_map = False

        selected_object = state.get("selected_object")

        if selected_object and self.map:
            self._updating_map = True
            try:
                self.highlight_selected_object(selected_object, preserve_zoom=True)
            finally:
                self._updating_map = False
        elif selected_object is None and self.selected_layer:
            self.clear_selection()


        map_center = state.get("map_center")
        map_zoom = state.get("map_zoom")

        if self.map and map_center and isinstance(map_center, list) and len(map_center) == 2 and not self._updating_map:
            current_center = self.map.getCenter()
            current_zoom = self.map.getZoom()

            try:
                center_lat_changed = abs(current_center.lat - map_center[0]) > 0.0001
                center_lng_changed = abs(current_center.lng - map_center[1]) > 0.0001
                zoom_changed = map_zoom is not None and current_zoom != map_zoom
            except Exception as e:
                error(f"Error comparing map coordinates: {e}")
                center_lat_changed = True
                center_lng_changed = True
                zoom_changed = map_zoom is not None

            if center_lat_changed or center_lng_changed or zoom_changed:
                self._updating_map = True
                try:
                    new_zoom = map_zoom if map_zoom is not None else current_zoom
                    self.map.setView([map_center[0], map_center[1]], new_zoom)
                    log(f"Updated map view to center: {map_center}, zoom: {new_zoom}")
                except Exception as e:
                    error(f"Error updating map view: {e}")
                finally:
                    self._updating_map = False

    def update_geo_layers(self, geo_objects, preserve_zoom=False):
        try:
            current_zoom = None
            current_center = None
            if preserve_zoom and self.map:
                current_zoom = self.map.getZoom()
                current_center = self.map.getCenter()

            if 'main' in self.layers and self.layers['main']:
                try:
                    self.map.removeLayer(self.layers['main'])
                except Exception as e:
                    log(f"Error removing existing layer: {e}")
                self.layers['main'] = None

            js.eval("""
            window.roleColors = {
                "highway:residential": "#e6194b",
                "way": "#3cb44b",
                "landuse:residential": "#ffe119",
                "highway:unclassified": "#ff7f00",
                "building:yes": "#f58231",
                "highway:primary": "#911eb4",
                "railway:rail": "#000000",
                "building:apartments": "#42d4f4",
                "building:house": "#fabebe",
                "highway:tertiary": "#469990",
                "highway:footway": "#9a6324",
                "waterway:river": "#0000ff",
                "highway:service": "#800000",
                "highway:secondary": "#e6beff",
                "highway:trunk": "#f032e6",
                "building:church": "#808000",
                "natural:water": "#000080",
                "highway:pedestrian": "#ffe119",
                "railway:subway": "#aaffc3",
                "building:school": "#4ed364",
                "waterway:dock": "#3e82fc",
                "landuse:grass": "#00ff00"
            };
            
            window.prefixColors = {
                "highway:": "#e6194b",
                "building:": "#f58231",
                "waterway:": "#0000ff",
                "railway:": "#000000",
                "landuse:": "#3cb44b",
                "natural:": "#4363d8",
                "amenity:": "#ffe119"
            };
            
            window.getColor = function(role) {
                if (!role) return "#3388ff";
                
                if (window.roleColors[role]) {
                    return window.roleColors[role];
                }
                
                for (var prefix in window.prefixColors) {
                    if (role.startsWith(prefix)) {
                        return window.prefixColors[prefix];
                    }
                }
                
                return "#3388ff";
            };
            
            window.colorizeMap = function() {
                function applyColors() {
                    var svgElements = document.querySelectorAll('#map-container svg');
                    
                    if (svgElements.length === 0) {
                        setTimeout(applyColors, 500);
                        return;
                    }
                    
                    for (var i = 0; i < svgElements.length; i++) {
                        var paths = svgElements[i].querySelectorAll('path');
                        
                        for (var j = 0; j < paths.length; j++) {
                            var path = paths[j];
                            var role = path.getAttribute('data-role');
                            var pathData = path.getAttribute('d');
                            var isPolygon = pathData && pathData.toLowerCase().indexOf('z') !== -1;
                            
                            if (role) {
                                var color = window.getColor(role);
                                path.setAttribute('stroke', color);
                                path.setAttribute('stroke-width', '2');
                                
                                if (!isPolygon || role.startsWith('highway:') || role.startsWith('railway:') || role.startsWith('waterway:')) {
                                    path.setAttribute('fill', 'none');
                                    path.setAttribute('fill-opacity', '0');
                                } else {
                                    path.setAttribute('fill', color);
                                    path.setAttribute('fill-opacity', '0.2');
                                }
                            }
                            else if (path.classList.contains('leaflet-interactive')) {
                                var colors = [
                                    "#ff8080", "#a0c8a0", "#c0c0ff", "#804000", "#ff0000",
                                    "#000000", "#a05000", "#c08060", "#ffc080", "#f0c0c0",
                                    "#0080ff", "#c8c8c8", "#ffff00", "#ff00ff", "#800080",
                                    "#0000ff", "#ffc0c0", "#404040", "#ff8000", "#00c0ff"
                                ];
                                
                                var colorIndex = j % colors.length;
                                var color = colors[colorIndex];
                                
                                path.setAttribute('stroke', color);
                                path.setAttribute('stroke-width', '2');
                                
                                if (!isPolygon) {
                                    path.setAttribute('fill', 'none');
                                    path.setAttribute('fill-opacity', '0');
                                } else {
                                    path.setAttribute('fill', color);
                                    path.setAttribute('fill-opacity', '0.2');
                                }
                            }
                        }
                    }
                }
                
                setTimeout(applyColors, 100);
            };
            
            if (!window._leafletEventsPatched) {
                window._leafletEventsPatched = true;
                
                var originalInitPath = L.SVG.prototype._initPath;
                
                L.SVG.prototype._initPath = function(layer) {
                    originalInitPath.call(this, layer);
                    
                    if (layer.feature && layer.feature.properties && layer.feature.properties.role) {
                        var role = layer.feature.properties.role;
                        var color = window.getColor(role);
                        
                        layer._path.setAttribute('data-role', role);
                        
                        var geometryType = '';
                        if (layer.feature && layer.feature.geometry) {
                            geometryType = layer.feature.geometry.type;
                        }
                        
                        layer._path.setAttribute('stroke', color);
                        layer._path.setAttribute('stroke-width', '2');
                        
                        if (geometryType === 'LineString' || geometryType === 'MultiLineString') {
                            layer._path.setAttribute('fill', 'none');
                            layer._path.setAttribute('fill-opacity', '0');
                        } else {
                            layer._path.setAttribute('fill', color);
                            layer._path.setAttribute('fill-opacity', '0.2');
                        }
                    }
                };
                
                var originalUpdateStyle = L.Path.prototype._updateStyle;
                
                L.Path.prototype._updateStyle = function() {
                    originalUpdateStyle.call(this);
                    
                    if (this.feature && this.feature.properties && this.feature.properties.role) {
                        var role = this.feature.properties.role;
                        var color = window.getColor(role);
                        
                        var geometryType = '';
                        if (this.feature && this.feature.geometry) {
                            geometryType = this.feature.geometry.type;
                        }
                        
                        this._path.setAttribute('stroke', color);
                        this._path.setAttribute('stroke-width', '2');
                        
                        if (geometryType === 'LineString' || geometryType === 'MultiLineString') {
                            this._path.setAttribute('fill', 'none');
                            this._path.setAttribute('fill-opacity', '0');
                        } else {
                            this._path.setAttribute('fill', color);
                            this._path.setAttribute('fill-opacity', '0.2');
                        }
                    }
                };
            }
            """)

            geo_json_str = json.dumps(geo_objects)
            geo_json_obj = js.JSON.parse(geo_json_str)

            def feature_handler_with_role(feature, layer):
                try:
                    self.feature_interaction_handler(feature, layer)
                    
                    js.eval("""
                    function setStyleByRole(feature, layer) {
                        if (feature.properties && feature.properties.role) {
                            var role = feature.properties.role;
                            var color = window.getColor(role);
                            
                            if (layer.setStyle) {
                                layer.setStyle({
                                    color: color,
                                    weight: 2,
                                    opacity: 0.7,
                                    fillColor: color,
                                    fillOpacity: 0.2
                                });
                            }
                            
                            if (layer._path) {
                                layer._path.setAttribute('data-role', role);
                                layer._path.setAttribute('stroke', color);
                                layer._path.setAttribute('fill', color);
                            }
                        }
                    }
                    """)
                    
                    js.eval("setStyleByRole(feature, layer)")
                except Exception as e:
                    log(f"Error in feature handler: {e}")
            
            feature_handler_proxy = create_proxy(feature_handler_with_role)

            try:
                layer = js.L.geoJSON(geo_json_obj, {
                    "onEachFeature": feature_handler_proxy
                })
            except Exception as e:
                log(f"Error creating GeoJSON layer: {e}")
                return

            layer.addTo(self.map)
            self.layers['main'] = layer
            
            js.window.colorizeMap()
            
            js.eval("""
            setTimeout(window.colorizeMap, 500);
            setTimeout(window.colorizeMap, 1000);
            setTimeout(window.colorizeMap, 2000);
            """)

            if not preserve_zoom:
                try:
                    bounds = layer.getBounds()
                    if bounds and hasattr(bounds, 'isValid') and bounds.isValid():
                        self.map.fitBounds(bounds)
                except Exception as e:
                    log(f"Could not fit map to bounds: {e}")
            else:
                if current_zoom is not None and current_center is not None:
                    try:
                        self.map.setView([current_center.lat, current_center.lng], current_zoom)
                    except Exception as e:
                        log(f"Error restoring zoom and center: {e}")

            try:
                feature_handler_proxy.destroy()
            except Exception as e:
                log(f"Error destroying proxy: {e}")

        except Exception as e:
            import traceback
            log(f"Error updating geo layers: {str(e)}")
            log(traceback.format_exc())

    def _on_feature_click(self, event, feature):
        """
        Обработчик клика по объекту на карте
        """
        try:
            log(f"Feature clicked: {feature.get('properties', {}).get('name', 'Unknown')}")
            
            event.stopPropagation()
            
            from ..actions.geo_actions import GeoActions
            GeoActions.select_geo_object(feature)
            
            from ..store.app_store import AppStore
            store = AppStore()
            state = store.get_state()
            
            if not state.get("info_panel_open", False):
                from ..dispatch.dispatcher import Dispatcher
                dispatcher = Dispatcher()
                dispatcher.dispatch("TOGGLE_INFO_PANEL", True)
        except Exception as e:
            error(f"Error in feature click handler: {e}")

    def feature_interaction_handler(self, feature, layer):
        """
        Handle interactions for each feature.

        Args:
            feature: The feature to attach events
            layer: The Leaflet layer
        """
        try:
            click_handler = create_proxy(lambda e, feature=feature: self._on_feature_click(e, feature))
            layer.on("click", click_handler)
            
            if not hasattr(layer, '_click_handlers'):
                layer._click_handlers = []
            layer._click_handlers.append(click_handler)
        except Exception as e:
            error(f"Error setting up feature interaction: {e}")


    def highlight_selected_object(self, selected_object, preserve_zoom=False):
        """
        Highlight the selected object on the map

        Args:
            selected_object: GeoJSON Feature to highlight
            preserve_zoom: Whether to preserve current zoom level
        """
        self.clear_selection()

        if preserve_zoom and self.map:
            current_zoom = self.map.getZoom()
            current_center = self.map.getCenter()

        try:
            if isinstance(selected_object, str):
                selected_object = json.loads(selected_object)

            properties = selected_object.get("properties", {})
            role = properties.get("role", "")
            base_color = self._get_color_for_role(role)

            highlight_style = {
                "color": "#ff0000",
                "weight": 4,
                "opacity": 1,
                "fillColor": base_color,
                "fillOpacity": 0.5
            }

            self.selected_layer = js.L.geoJSON(selected_object, {"style": highlight_style})

            self.selected_layer.addTo(self.map)
            self.selected_layer.bringToFront()

            if not preserve_zoom:
                bounds = self.selected_layer.getBounds()
                if bounds.isValid():
                    self.map.fitBounds(bounds, {"padding": [50, 50]})
            else:
                if 'current_zoom' in locals() and 'current_center' in locals():
                    try:
                        self.map.setView([current_center.lat, current_center.lng], current_zoom)
                    except Exception as e:
                        error(f"Error restoring zoom and center: {e}")

        except Exception as e:
            error(f"Error highlighting selected object: {str(e)}")

    def clear_selection(self):
        """Clear the currently selected object"""
        if self.selected_layer:
            try:
                self.map.removeLayer(self.selected_layer)
            except Exception as e:
                error(f"Error clearing selection: {e}")
            self.selected_layer = None

    def on_map_click(self, event):
        """
        Handle map click event

        Args:
            event: Leaflet click event
        """
        if self._updating_map:
            return

        if self.popup:
            self.map.closePopup(self.popup)
            self.popup = None

        self.store.update_state({"selected_object": None})

    def on_map_zoom(self, event):
        """
        Handle map zoom event

        Args:
            event: Leaflet zoom event
        """

        if self._updating_map:
            log("Ignoring zoom event during programmatic update")
            return

        center = self.map.getCenter()
        zoom = self.map.getZoom()
        self._updating_map = True
        try:
            CityActions.update_map_view(
                [center.lat, center.lng],
                zoom
            )
        finally:
            self._updating_map = False

    def on_map_move(self, event):
        """
        Handle map move event

        Args:
            event: Leaflet move event
        """

        if self._updating_map:
            log("Ignoring move event during programmatic update")
            return

        center = self.map.getCenter()
        zoom = self.map.getZoom()
        self._updating_map = True
        try:
            CityActions.update_map_view(
                [center.lat, center.lng],
                zoom
            )
        finally:
            self._updating_map = False
