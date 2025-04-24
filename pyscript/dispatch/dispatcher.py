"""
Dispatcher for updating the store
"""
from ..store.app_store import AppStore
from ..utils.logging import log

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
        log(f"Dispatching action: {action_type}")

        if action_type.endswith("_REQUEST"):
            self._store.update_state({"loading": True, "error": None})

        if action_type == "NAVIGATE_TO_SIMULATION":
            self._store.update_state({
                "navigate_to_simulation": payload,
                "current_view": "simulation",
                "loading": False
            })

        elif action_type == "NAVIGATE_TO_HOME":
            self._store.update_state({
                "current_view": "home",
                "loading": False
            })

        elif action_type == "RESET_NAVIGATION":
            self._store.update_state({
                "navigate_to_simulation": False,
                "loading": False
            })

        elif action_type == "SELECT_MODE":
            self._store.update_state({
                "selected_mode_id": payload,
                "loading": False
            })

        elif action_type == "CLEAR_SELECTION":
            self._store.update_state({
                "selected_object": None,
                "loading": False
            })

        elif action_type == "SET_CITIES":
            self._store.update_state({"cities": payload, "loading": False})

        elif action_type == "SELECT_CITY":
            self._store.update_state({
                "selected_city_id": payload['id'],
                "selected_city_data": payload,
                "selected_year": None,
                "simulation": None,
                "geo_objects": None,
                "selected_object": None,
                "loading": False
            })
        elif action_type == "SELECT_GEO_OBJECT":
            self._store.update_state({"selected_object": payload})
        
        elif action_type == "TOGGLE_INFO_PANEL":
             self._store.update_state({"info_panel_open": payload})

        elif action_type == "SET_AVAILABLE_YEARS":
            self._store.update_state({"available_years": payload, "loading": False})

        elif action_type == "SET_ANIMATION_STATE":
            if payload is None:
                payload = {"active": False}
            elif isinstance(payload, bool):
                payload = {"active": payload}

        elif action_type == "SELECT_YEAR":
            self._store.update_state({
                "selected_year": payload,
                "simulation": None,
                "geo_objects": None,
                "selected_object": None,
                "loading": False
            })

        elif action_type == "SELECT_MODE_HOME":
            self._store.update_state({
                "selected_mode_id": payload,
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
            if payload is not None:
                self._store.update_state({**payload, "loading": False})
