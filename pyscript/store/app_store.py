"""
Application state store using Flux architecture
"""
import js
from pyodide.ffi import create_proxy


class AppStore:
    """Centralized store for application state"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppStore, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the store with default values"""
        self._state = {
            "loading": False,
            "error": None,

            "cities": [],
            "selected_city_id": None,
            "available_years": [],
            "selected_year": None,
            "simulation": None,
            "geo_objects": None,
            "selected_object": None,

            "map_center": None,
            "map_zoom": None,
            "info_panel_open": False
        }

        self._subscribers = []

    def get_state(self):
        """Get the current state"""
        return self._state.copy()

    def subscribe(self, callback):
        """
        Subscribe to state changes
        
        Args:
            callback: Function to call when state changes
            
        Returns:
            Unsubscribe function
        """
        if callable(callback):
            proxy_callback = create_proxy(callback)
            self._subscribers.append(proxy_callback)

            def unsubscribe():
                if proxy_callback in self._subscribers:
                    self._subscribers.remove(proxy_callback)
                    proxy_callback.destroy()

            return unsubscribe

    def update_state(self, update_dict):
        """
        Update the state with new values
        
        Args:
            update_dict: Dictionary of state keys and values to update
        """
        self._state.update(update_dict)

        for subscriber in self._subscribers:
            subscriber(self._state)

    def get_cities(self):
        """Get the list of cities"""
        return self._state["cities"]

    def get_selected_city(self):
        """Get the currently selected city"""
        city_id = self._state["selected_city_id"]
        if not city_id:
            return None

        for city in self._state["cities"]:
            if city["id"] == city_id:
                return city

        return None

    def get_selected_year(self):
        """Get the currently selected year"""
        return self._state["selected_year"]

    def get_geo_objects(self):
        """Get the geographic objects for the current simulation"""
        return self._state["geo_objects"]

    def get_selected_object(self):
        """Get the currently selected geographic object"""
        return self._state["selected_object"]
