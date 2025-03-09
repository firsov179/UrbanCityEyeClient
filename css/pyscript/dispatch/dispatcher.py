"""
Dispatcher for updating the store
"""
from ..store.app_store import AppStore

class Dispatcher:
    """
    Dispatcher for updating the store based on actions
    Follows the Flux architecture pattern
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Dispatcher, cls).__new__(cls)
            cls._instance._store = AppStore()
        return cls._instance
    
    def dispatch(self, action_type, payload=None):
        """
        Dispatch an action to update the store
        
        Args:
            action_type: Type of action to dispatch
            payload: Data payload for the action
        """
        print(f"Dispatching action: {action_type}")
        
        # Set loading state based on action type
        if action_type.endswith("_REQUEST"):
            self._store.update_state({"loading": True, "error": None})
        
        # Handle different action types
        if action_type == "SET_CITIES":
            self._store.update_state({"cities": payload, "loading": False})
            
        elif action_type == "SELECT_CITY":
            self._store.update_state({
                "selected_city_id": payload,
                "selected_year": None,
                "simulation": None,
                "geo_objects": None,
                "selected_object": None,
                "loading": False
            })
            
        elif action_type == "SET_AVAILABLE_YEARS":
            self._store.update_state({"available_years": payload, "loading": False})
            
        elif action_type == "SELECT_YEAR":
            self._store.update_state({
                "selected_year": payload,
                "simulation": None,
                "geo_objects": None,
                "selected_object": None,
                "loading": False
            })
            
        elif action_type == "SET_SIMULATION":
            self._store.update_state({"simulation": payload, "loading": False})
            
        elif action_type == "SET_GEO_OBJECTS":
            self._store.update_state({"geo_objects": payload, "loading": False})
            
        elif action_type == "SELECT_OBJECT":
            self._store.update_state({"selected_object": payload, "loading": False})
            
        elif action_type == "SET_MAP_VIEW":
            self._store.update_state({
                "map_center": payload.get("center"),
                "map_zoom": payload.get("zoom"),
                "loading": False
            })
            
        elif action_type == "TOGGLE_INFO_PANEL":
            current = self._store.get_state()["info_panel_open"]
            self._store.update_state({
                "info_panel_open": not current if payload is None else payload,
                "loading": False
            })
            
        elif action_type == "API_ERROR":
            self._store.update_state({"error": payload, "loading": False})
            
        else:
            # Generic state update for custom actions
            if payload is not None:
                self._store.update_state({**payload, "loading": False})

