"""
Actions related to cities
"""
import asyncio
from ..utils.api_client import APIClient
from ..dispatch.dispatcher import Dispatcher
from ..utils.logging import log, error
from .geo_actions import GeoActions

class CityActions:
    """Actions for managing cities"""

    @staticmethod
    async def select_city_simulation(city_id, year, mode_id):
        """
        Select a city and load all related data for simulation

        Args:
            city_id: ID of the city to select
        """
        await CityActions.fetch_simulation(city_id, year, mode_id)

    @staticmethod
    def navigate_to_home():
        """Navigate back to home screen"""
        dispatcher = Dispatcher()
        dispatcher.dispatch("NAVIGATE_TO_HOME")

    @staticmethod
    def select_mode(mode_id):
        """
        Select a simulation mode

        Args:
            mode_id: ID of the mode to select (1=Transport, 2=Housing)
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("SELECT_MODE", mode_id)

    @staticmethod
    async def fetch_cities():
        """
        Fetch all cities from the API
        
        Returns:
            List of cities or None if the request fails
        """
        log("Fetching cities...")
        dispatcher = Dispatcher()
        dispatcher.dispatch("CITIES_REQUEST")

        response = await APIClient.get("cities/")

        if response:
            log(f"Received {len(response)} cities")
            dispatcher.dispatch("SET_CITIES", response)
            return response
        else:
            error("Failed to fetch cities")
            dispatcher.dispatch("API_ERROR", "Failed to fetch cities")
            return None

    @staticmethod
    async def select_city(city_id):
        """
        Select a city

        Args:
            city_id: ID of the city to select
        """
        from ..store.app_store import AppStore
        store = AppStore()
        state = store.get_state()

        current_view = state.get("current_view", "home")

        response = await APIClient.get(f"cities/{city_id}")
        dispatcher = Dispatcher()

        if response:
            dispatcher.dispatch("SELECT_CITY", response)
        else:
            error("Failed to fetch cities")
            dispatcher.dispatch("API_ERROR", f"Failed to fetch city with id {city_id}")

        if current_view == "simulation":
            await CityActions.fetch_available_years(city_id)

    @staticmethod
    async def fetch_available_years(city_id):
        """
        Fetch available years for a city
        
        Args:
            city_id: ID of the city
            
        Returns:
            List of available years or None if the request fails
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("YEARS_REQUEST")

        response = await APIClient.get(f"simulations/city/{city_id}/years")

        if response:
            dispatcher.dispatch("SET_AVAILABLE_YEARS", response)

            if response and len(response) > 0:
                CityActions.select_year(city_id, response[0])

            return response
        else:
            dispatcher.dispatch("API_ERROR", f"Failed to fetch years for city {city_id}")
            return None

    @staticmethod
    def select_year(city_id, year):
        """
        Select a year for the current city
        
        Args:
            city_id: ID of the city
            year: Year to select
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("SELECT_YEAR", year)

    @staticmethod
    async def fetch_simulation(city_id, year, mode_id):
        """
        Fetch simulation data for a city and year
        
        Args:
            city_id: ID of the city
            year: Year of the simulation
            
        Returns:
            Simulation data or None if the request fails
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("SIMULATION_REQUEST")

        response = await APIClient.get(f"simulations/city/{city_id}/year/{year}/mode/{mode_id}")

        if response:
            dispatcher.dispatch("SET_SIMULATION", response)

            if "id" in response:
                asyncio.ensure_future(CityActions.fetch_geo_objects(response["id"]))

            return response
        else:
            dispatcher.dispatch("API_ERROR", f"Failed to fetch simulation for city {city_id}, year {year}, mode {mode_id}")
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
    def select_geo_object(geo_object, center_map=True):
        """
        Select a geographic object and optionally center the map on it
        
        Args:
            geo_object: GeoJSON Feature to select
            center_map: Whether to center the map on the object
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("SELECT_GEO_OBJECT", geo_object)
        dispatcher.dispatch("TOGGLE_INFO_PANEL", True)

        if center_map and geo_object:
            try:
                geometry = geo_object.get("geometry", {})
                center = GeoActions.get_geometry_center(geometry)

                if center:
                    dispatcher.dispatch("SET_MAP_VIEW", {"center": center})
            except Exception as e:
                error(f"Error centering map on object: {str(e)}")

    @staticmethod
    async def fetch_city_details(city_id):
        """
        Fetch detailed information about a city
        
        Args:
            city_id: ID of the city
            
        Returns:
            City details or None if the request fails
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("CITY_DETAILS_REQUEST")

        response = await APIClient.get(f"cities/{city_id}")

        if response:
            dispatcher.dispatch("SET_CITY_DETAILS", response)
            return response
        else:
            dispatcher.dispatch("API_ERROR", f"Failed to fetch details for city {city_id}")
            return None

    @staticmethod
    async def fetch_geo_object_details(geo_object_id):
        """
        Fetch detailed information about a geographic object
        
        Args:
            geo_object_id: ID of the geographic object
            
        Returns:
            Object details or None if the request fails
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("OBJECT_DETAILS_REQUEST")

        response = await APIClient.get(f"geo-objects/{geo_object_id}")

        if response:
            dispatcher.dispatch("SET_OBJECT_DETAILS", response)
            return response
        else:
            dispatcher.dispatch("API_ERROR", f"Failed to fetch details for geo object {geo_object_id}")
            return None

    @staticmethod
    def update_map_view(center, zoom):
        """
        Update the map view (center point and zoom level)
        
        Args:
            center: [lat, lng] center coordinates
            zoom: Zoom level
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("SET_MAP_VIEW", {"center": center, "zoom": zoom})

    @staticmethod
    def toggle_info_panel(is_open=None):
        """
        Toggle the info panel open/closed state
        
        Args:
            is_open: Optional explicit state (True=open, False=closed)
                     If None, toggles the current state
        """
        dispatcher = Dispatcher()
        dispatcher.dispatch("TOGGLE_INFO_PANEL", is_open)
