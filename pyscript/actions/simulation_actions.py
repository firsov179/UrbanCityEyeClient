"""
Actions related to simulations and timeline functionality
"""
import asyncio
from ..utils.api_client import APIClient
from ..dispatch.dispatcher import Dispatcher
from ..utils.logging import *


class SimulationActions:
    """Actions for managing simulations and timeline interactions"""

    @staticmethod
    async def fetch_all_simulations():
        """
        Fetch all simulations from the API
        
        Returns:
            List of simulations or None if the request fails
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("ALL_SIMULATIONS_REQUEST")

        response = await APIClient.get("simulations")

        if response:
            dispatcher.dispatch("SET_ALL_SIMULATIONS", response)
            return response
        else:
            dispatcher.dispatch("API_ERROR", "Failed to fetch simulations")
            return None

    @staticmethod
    async def fetch_geo_objects(simulation_id, bbox=None):
        """
        Fetch geographic objects for a simulation
        
        Args:
            simulation_id: ID of the simulation
            bbox: Optional bounding box [minx, miny, maxx, maxy]
            
        Returns:
            GeoJSON data or None if the request fails
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("GEO_OBJECTS_REQUEST")

        params = {}
        if bbox:
            params = {
                "minx": bbox[0],
                "miny": bbox[1],
                "maxx": bbox[2],
                "maxy": bbox[3]
            }

        response = await APIClient.get(f"geo-objects/simulation/{simulation_id}", params)

        if response:
            dispatcher.dispatch("SET_GEO_OBJECTS", response)
            return response
        else:
            dispatcher.dispatch("API_ERROR", f"Failed to fetch geo objects for simulation {simulation_id}")
            return None

    @staticmethod
    def generate_timeline(years, step=5):
        """
        Generate a timeline with markers based on available years
        
        Args:
            years: List of available years
            step: Step between main timeline markers
            
        Returns:
            Dictionary with timeline information
        """
        if not years or len(years) == 0:
            return {"markers": [], "range": [0, 0]}

        sorted_years = sorted(years)
        min_year = sorted_years[0]
        max_year = sorted_years[-1]

        markers = []
        for year in range(min_year, max_year + 1):
            is_available = year in sorted_years
            is_major = (year % step == 0)

            if is_available or is_major:
                markers.append({
                    "year": year,
                    "is_available": is_available,
                    "is_major": is_major
                })

        timeline_data = {
            "markers": markers,
            "range": [min_year, max_year]
        }

        dispatcher = Dispatcher()
        dispatcher.dispatch("SET_TIMELINE", timeline_data)

        return timeline_data

    @staticmethod
    def jump_to_next_year():
        """
        Jump to the next available year in the timeline
        """
        from ..store.app_store import AppStore

        store = AppStore()
        state = store.get_state()

        current_year = state["selected_year"]
        available_years = state["available_years"]
        city_id = state["selected_city_id"]

        if not current_year or not available_years or len(available_years) == 0:
            return

        sorted_years = sorted(available_years)

        next_year = None
        for year in sorted_years:
            if year > current_year:
                next_year = year
                break

        if next_year is None and len(sorted_years) > 0:
            next_year = sorted_years[0]

        if next_year is not None:
            from .city_actions import CityActions
            CityActions.select_year(city_id, next_year)

    @staticmethod
    def jump_to_previous_year():
        """
        Jump to the previous available year in the timeline
        """
        from ..store.app_store import AppStore

        store = AppStore()
        state = store.get_state()

        current_year = state["selected_year"]
        available_years = state["available_years"]
        city_id = state["selected_city_id"]

        if not current_year or not available_years or len(available_years) == 0:
            return

        sorted_years = sorted(available_years, reverse=True)

        prev_year = None
        for year in sorted_years:
            if year < current_year:
                prev_year = year
                break

        if prev_year is None and len(sorted_years) > 0:
            prev_year = sorted_years[0]

        if prev_year is not None:
            from .city_actions import CityActions
            CityActions.select_year(city_id, prev_year)

    @staticmethod
    async def start_timeline_animation(delay=1000):
        """
        Start an animation through the timeline

        Args:
            delay: Delay between years in milliseconds
        """
        from ..store.app_store import AppStore

        store = AppStore()
        state = store.get_state()

        dispatcher = Dispatcher()
        dispatcher.dispatch("SET_ANIMATION_STATE", {"active": True})


        available_years = state.get("available_years", [])
        city_id = state.get("selected_city_id")

        if not available_years or len(available_years) == 0 or not city_id:
            dispatcher.dispatch("SET_ANIMATION_STATE", {"active": False})
            return

        sorted_years = sorted(available_years)

        from .city_actions import CityActions

        try:
            for year in sorted_years:
                current_state = store.get_state()

                animation_active = False
                animation_state = current_state.get("animation_active")

                if isinstance(animation_state, dict):
                    animation_active = animation_state.get("active", False)
                else:
                    animation_active = bool(animation_state)

                if not animation_active:
                    break

                CityActions.select_year(city_id, year)

        finally:
            dispatcher.dispatch("SET_ANIMATION_STATE", {"active": False})

    @staticmethod
    def stop_timeline_animation():
        """
        Stop the timeline animation
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("SET_ANIMATION_STATE", {"active": False})

