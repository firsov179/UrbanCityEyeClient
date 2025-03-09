"""
Actions related to simulations and timeline functionality
"""
import asyncio
from ..utils.api_client import APIClient
from ..dispatch.dispatcher import Dispatcher

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
    async def fetch_simulation_by_id(simulation_id):
        """
        Fetch a specific simulation by ID
        
        Args:
            simulation_id: ID of the simulation
            
        Returns:
            Simulation data or None if the request fails
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("SIMULATION_REQUEST")
        
        response = await APIClient.get(f"simulations/{simulation_id}")
        
        if response:
            dispatcher.dispatch("SET_SIMULATION", response)
            
            # After fetching simulation, get geo objects for this simulation
            asyncio.ensure_future(SimulationActions.fetch_geo_objects(simulation_id))
            
            return response
        else:
            dispatcher.dispatch("API_ERROR", f"Failed to fetch simulation {simulation_id}")
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
        
        # Prepare query parameters if bbox is provided
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
        
        # Sort years
        sorted_years = sorted(years)
        min_year = sorted_years[0]
        max_year = sorted_years[-1]
        
        # Generate markers
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
        
        # Sort years
        sorted_years = sorted(available_years)
        
        # Find the next year
        next_year = None
        for year in sorted_years:
            if year > current_year:
                next_year = year
                break
        
        # If there's no next year, loop back to the first
        if next_year is None and len(sorted_years) > 0:
            next_year = sorted_years[0]
        
        # If we found a next year, select it
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
        
        # Sort years
        sorted_years = sorted(available_years, reverse=True)
        
        # Find the previous year
        prev_year = None
        for year in sorted_years:
            if year < current_year:
                prev_year = year
                break
        
        # If there's no previous year, loop back to the last
        if prev_year is None and len(sorted_years) > 0:
            prev_year = sorted_years[0]
        
        # If we found a previous year, select it
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
        
        # Set animation state
        dispatcher = Dispatcher()
        dispatcher.dispatch("SET_ANIMATION_STATE", True)
        
        # Get available years and city
        available_years = state["available_years"]
        city_id = state["selected_city_id"]
        
        if not available_years or len(available_years) == 0 or not city_id:
            dispatcher.dispatch("SET_ANIMATION_STATE", False)
            return
        
        # Sort years
        sorted_years = sorted(available_years)
        
        # Animate through each year
        from .city_actions import CityActions
        
        try:
            for year in sorted_years:
                # Check if animation is still active
                current_state = store.get_state()
                if not current_state.get("animation_active", False):
                    break
                
                # Select the year
                CityActions.select_year(city_id, year)
                
                # Wait for the specified delay
                await asyncio.sleep(delay / 1000)  # Convert ms to seconds
        finally:
            # Ensure animation state is reset when done
            dispatcher.dispatch("SET_ANIMATION_STATE", False)
    
    @staticmethod
    def stop_timeline_animation():
        """
        Stop the timeline animation
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("SET_ANIMATION_STATE", False)
    
    @staticmethod
    def compare_years(year1, year2):
        """
        Set up a comparison between two years
        
        Args:
            year1: First year to compare
            year2: Second year to compare
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("SET_COMPARISON_YEARS", {"year1": year1, "year2": year2})
        
        # Set up comparison mode
        dispatcher.dispatch("SET_COMPARISON_MODE", True)
        
        # Fetch data for both years
        from ..store.app_store import AppStore
        
        store = AppStore()
        city_id = store.get_state()["selected_city_id"]
        
        if city_id:
            from .city_actions import CityActions
            
            # We need to fetch simulation data for both years
            asyncio.ensure_future(SimulationActions.fetch_comparison_data(city_id, year1, year2))
    
    @staticmethod
    async def fetch_comparison_data(city_id, year1, year2):
        """
        Fetch data for comparing two years
        
        Args:
            city_id: ID of the city
            year1: First year
            year2: Second year
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("COMPARISON_DATA_REQUEST")
        
        # Fetch simulations for both years
        sim1_response = await APIClient.get(f"simulations/city/{city_id}/year/{year1}")
        sim2_response = await APIClient.get(f"simulations/city/{city_id}/year/{year2}")
        
        if not sim1_response or not sim2_response:
            dispatcher.dispatch("API_ERROR", "Failed to fetch comparison data")
            return None
        
        # Fetch geo objects for both simulations
        geo1_response = None
        geo2_response = None
        
        if "id" in sim1_response:
            geo1_response = await APIClient.get(f"geo-objects/simulation/{sim1_response['id']}")
        
        if "id" in sim2_response:
            geo2_response = await APIClient.get(f"geo-objects/simulation/{sim2_response['id']}")
        
        if not geo1_response or not geo2_response:
            dispatcher.dispatch("API_ERROR", "Failed to fetch geo objects for comparison")
            return None
        
        # Prepare comparison data
        comparison_data = {
            "simulation1": sim1_response,
            "simulation2": sim2_response,
            "geo_objects1": geo1_response,
            "geo_objects2": geo2_response
        }
        
        dispatcher.dispatch("SET_COMPARISON_DATA", comparison_data)
        return comparison_data
    
    @staticmethod
    def exit_comparison_mode():
        """
        Exit the comparison mode and return to normal view
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("SET_COMPARISON_MODE", False)
        dispatcher.dispatch("SET_COMPARISON_DATA", None)
        dispatcher.dispatch("SET_COMPARISON_YEARS", None)

