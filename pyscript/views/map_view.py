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

        # Initialize the Leaflet map
        self.create_map()

        # Subscribe to store changes
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

        # Clear the handler dictionary
        self._proxy_handlers = {}

    def _setup_event_handlers(self):
        """Set up event handlers for the map with proper proxy management"""

        # Create and save proxy objects
        self._proxy_handlers['click'] = create_proxy(self.on_map_click)
        self._proxy_handlers['zoomend'] = create_proxy(self.on_map_zoom)
        self._proxy_handlers['moveend'] = create_proxy(self.on_map_move)

        # Add handlers to the map
        self.map.on("click", self._proxy_handlers['click'])
        self.map.on("zoomend", self._proxy_handlers['zoomend'])
        self.map.on("moveend", self._proxy_handlers['moveend'])

    def create_map(self):
        """Create the Leaflet map instance"""
        try:
            # Check if the container exists
            if not self.container:
                error(f"Error: Map container '{self.container_id}' not found in DOM")
                return

            # Remove existing map if it exists
            if self.map:
                log("Removing existing map instance")
                self._clear_event_handlers()
                try:
                    self.map.remove()
                except Exception as e:
                    error(f"Error removing old map: {e}")
                self.map = None

            # Ensure valid center coordinates
            if not MAP_DEFAULT_CENTER or len(MAP_DEFAULT_CENTER) != 2:
                center = [51.5074, -0.1278]  # Default London coordinates
                log(f"Using default center: {center}")
            else:
                center = MAP_DEFAULT_CENTER
                log(f"Using configured center: {center}")

            # Create Leaflet LatLng object for center
            center_obj = js.L.latLng(center[0], center[1])

            # Ensure valid zoom
            zoom = MAP_DEFAULT_ZOOM if isinstance(MAP_DEFAULT_ZOOM, int) else 13

            log(f"Creating map with center: {center}, zoom: {zoom}")
            self.map = js.L.map(self.container_id).setView(center_obj, zoom)

            # Add tile layer
            js.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                "attribution": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                "maxZoom": 19
            }).addTo(self.map)

            # Добавление стиля для скрытия флага Украины в атрибуции
            js.eval("""
            (function() {
                var style = document.createElement('style');
                style.textContent = '.leaflet-attribution-flag { display: none !important; }';
                document.head.appendChild(style);
            })();
            """)

            # Add event handlers with proxy preservation
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
        # Если карта обновляется программно, не реагируем на изменения состояния
        if self._updating_map:
            log("Skipping state update while map is being programmatically updated")
            return

        # Проверка на наличие новых гео-объектов
        geo_objects = state.get("geo_objects")

        if geo_objects and self.map:

            log(f"load {len(geo_objects)} geo_objects")
            # Сохраняем текущий зум перед обновлением слоя
            current_zoom = self.map.getZoom()

            # Устанавливаем флаг программного обновления
            self._updating_map = True
            try:
                # Обновляем слой с гео-объектами
                self.update_geo_layers(geo_objects.get('data', geo_objects), preserve_zoom=True)
            finally:
                # Сбрасываем флаг
                self._updating_map = False

        # Проверка на наличие выбранного объекта
        selected_object = state.get("selected_object")

        if selected_object and self.map:
            # Устанавливаем флаг программного обновления
            self._updating_map = True
            try:
                self.highlight_selected_object(selected_object, preserve_zoom=True)
            finally:
                # Сбрасываем флаг
                self._updating_map = False
        elif selected_object is None and self.selected_layer:
            self.clear_selection()

        # Обрабатываем изменение представления карты только если это явный запрос
        # (не при изменении года/гео-объектов)
        map_center = state.get("map_center")
        map_zoom = state.get("map_zoom")

        if self.map and map_center and isinstance(map_center, list) and len(map_center) == 2 and not self._updating_map:
            # Получение текущих значений карты
            current_center = self.map.getCenter()
            current_zoom = self.map.getZoom()

            # Проверяем, есть ли существенные изменения центра
            try:
                center_lat_changed = abs(current_center.lat - map_center[0]) > 0.0001
                center_lng_changed = abs(current_center.lng - map_center[1]) > 0.0001
                zoom_changed = map_zoom is not None and current_zoom != map_zoom
            except Exception as e:
                error(f"Error comparing map coordinates: {e}")
                center_lat_changed = True
                center_lng_changed = True
                zoom_changed = map_zoom is not None

            # Обновление представления карты только при наличии реальных изменений
            if center_lat_changed or center_lng_changed or zoom_changed:
                # Устанавливаем флаг программного обновления
                self._updating_map = True
                try:
                    # Используем только валидные координаты
                    new_zoom = map_zoom if map_zoom is not None else current_zoom
                    self.map.setView([map_center[0], map_center[1]], new_zoom)
                    log(f"Updated map view to center: {map_center}, zoom: {new_zoom}")
                except Exception as e:
                    error(f"Error updating map view: {e}")
                finally:
                    # Сбрасываем флаг
                    self._updating_map = False

    def update_geo_layers(self, geo_objects, preserve_zoom=False):
        """
        Update map layers with new geographic objects

        Args:
            geo_objects: GeoJSON FeatureCollection
            preserve_zoom: Whether to preserve current zoom level after update
        """
        try:
            # Сохраняем текущий зум и центр, если нужно
            if preserve_zoom and self.map:
                current_zoom = self.map.getZoom()
                current_center = self.map.getCenter()

            # Clear existing layers
            if 'main' in self.layers and self.layers['main']:
                try:
                    self.map.removeLayer(self.layers['main'])
                except Exception as e:
                    error(f"Error removing existing layer: {e}")
                self.layers['main'] = None

            # Конвертируем geo_objects в строку JSON, затем в JavaScript объект
            import json

            # Преобразуем в JSON строку
            geo_json_str = json.dumps(geo_objects)

            # Преобразуем JSON строку в JavaScript объект
            geo_json_obj = js.JSON.parse(geo_json_str)

            # Используем простые опции
            options = {
                "style": {
                    "color": "#3388ff",
                    "weight": 2,
                    "opacity": 0.7,
                    "fillOpacity": 0.2
                }
            }

            # Создаем слой с JavaScript объектом
            layer = js.L.geoJSON(geo_json_obj, options)

            # Добавляем слой на карту
            layer.addTo(self.map)

            # Сохраняем слой
            self.layers['main'] = layer

            # Устанавливаем границы карты только если не нужно сохранять зум
            if not preserve_zoom:
                try:
                    bounds = layer.getBounds()
                    if bounds and hasattr(bounds, 'isValid') and bounds.isValid():
                        self.map.fitBounds(bounds)
                except Exception as e:
                    log(f"Could not fit map to bounds: {e}")
            else:
                # Восстанавливаем зум и центр, если они были сохранены
                if 'current_zoom' in locals() and 'current_center' in locals():
                    try:
                        self.map.setView([current_center.lat, current_center.lng], current_zoom)
                    except Exception as e:
                        error(f"Error restoring zoom and center: {e}")

            log("GeoJSON layer updated successfully")

        except Exception as e:
            import traceback
            error(f"Error updating geo layers: {str(e)}")
            error(traceback.format_exc())

    def feature_interaction_handler(self, feature, layer):
        """
        Handle interactions for each feature.

        Args:
            feature: The feature to attach events
            layer: The Leaflet layer
        """
        # Example setup for click interaction:
        layer.on("click", lambda e: GeoActions.select_geo_object(feature))

    def highlight_selected_object(self, selected_object, preserve_zoom=False):
        """
        Highlight the selected object on the map

        Args:
            selected_object: GeoJSON Feature to highlight
            preserve_zoom: Whether to preserve current zoom level
        """
        # Clear previous selection
        self.clear_selection()

        # Сохраняем текущий зум и центр, если нужно
        if preserve_zoom and self.map:
            current_zoom = self.map.getZoom()
            current_center = self.map.getCenter()

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

            # Если не нужно сохранять зум, центрируем карту на выделенном объекте
            if not preserve_zoom:
                bounds = self.selected_layer.getBounds()
                if bounds.isValid():
                    self.map.fitBounds(bounds, {"padding": [50, 50]})
            else:
                # Восстанавливаем зум и центр, если они были сохранены
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
        # Если карта обновляется программно, игнорируем пользовательские клики
        if self._updating_map:
            return

        # Close popup if open
        if self.popup:
            self.map.closePopup(self.popup)
            self.popup = None

        # Clear selected object
        self.store.update_state({"selected_object": None})

    def on_map_zoom(self, event):
        """
        Handle map zoom event

        Args:
            event: Leaflet zoom event
        """
        # Если карта обновляется программно, не реагируем на события

        if self._updating_map:
            log("Ignoring zoom event during programmatic update")
            return

            # Получаем центр и зум
            center = self.map.getCenter()
            zoom = self.map.getZoom()
            # Устанавливаем флаг для предотвращения циклических обновлений
            self._updating_map = True
            try:
                # Update map zoom in the store
                CityActions.update_map_view(
                    [center.lat, center.lng],
                    zoom
                )
            finally:
                # Сбрасываем флаг
                self._updating_map = False

    def on_map_move(self, event):
        """
        Handle map move event

        Args:
            event: Leaflet move event
        """
        # Если карта обновляется программно, не реагируем на события

        if self._updating_map:
            log("Ignoring move event during programmatic update")
            return

        # Получаем центр и зум
        center = self.map.getCenter()
        zoom = self.map.getZoom()
        # Устанавливаем флаг для предотвращения циклических обновлений
        self._updating_map = True
        try:
            # Update map center in the store
            CityActions.update_map_view(
                [center.lat, center.lng],
                zoom
            )
        finally:
            # Сбрасываем флаг
            self._updating_map = False
