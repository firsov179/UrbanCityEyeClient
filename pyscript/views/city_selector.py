"""
City selector component that allows users to select a city
"""
import js
from pyodide.ffi import create_proxy
from ..store.app_store import AppStore
from ..actions.city_actions import CityActions
from ..utils.logging import warn


class CitySelector:
    """City selector component for the UI"""

    def __init__(self, container_id="city-selector-container"):
        """
        Initialize the city selector
        
        Args:
            container_id: ID of the HTML container element
        """
        self.container_id = container_id
        self.container = js.document.getElementById(container_id)
        self.store = AppStore()
        self.unsubscribe = None

    def initialize(self):
        """Initialize the component and subscribe to store updates"""
        if self.container is None:
            warn(f"Warning: Container {self.container_id} not found in the DOM")
            return

        # Fetch cities when initializing
        self.fetch_cities()

        # Subscribe to store changes
        self.unsubscribe = self.store.subscribe(create_proxy(self.on_state_change))

        # Initial render
        self.render()

    def on_state_change(self, state):
        """
        Handle state changes from the store
        
        Args:
            state: Current application state
        """
        self.render()

    def render(self):
        """Render the city selector component"""
        if self.container is None:
            return

        # Get the current state
        state = self.store.get_state()
        cities = state.get("cities", [])
        selected_city_id = state.get("selected_city_id")
        loading = state.get("loading", False)

        # Clear the container
        self.container.innerHTML = ""

        # Create the select element
        select_elem = js.document.createElement("select")
        select_elem.id = "city-select"
        select_elem.className = "city-selector"

        # Add a default option
        default_option = js.document.createElement("option")
        default_option.value = ""
        default_option.textContent = "-- Select a City --"
        default_option.disabled = True
        default_option.selected = selected_city_id is None
        select_elem.appendChild(default_option)

        # Add options for each city
        for city in cities:
            option = js.document.createElement("option")
            option.value = str(city["id"])
            option.textContent = city["name"]
            option.selected = selected_city_id == city["id"]
            select_elem.appendChild(option)

        # Add change event listener
        select_elem.onchange = create_proxy(self.on_city_change)

        # Create a wrapper for the selector
        wrapper = js.document.createElement("div")
        wrapper.className = "city-selector-wrapper"

        # Add a label
        label = js.document.createElement("label")
        label.htmlFor = "city-select"
        label.textContent = "City: "
        wrapper.appendChild(label)

        # Add the select element
        wrapper.appendChild(select_elem)

        # Add loading indicator if needed
        if loading:
            loading_elem = js.document.createElement("span")
            loading_elem.className = "loading-indicator"
            loading_elem.textContent = "Loading..."
            wrapper.appendChild(loading_elem)

        # Add the wrapper to the container
        self.container.appendChild(wrapper)

    def on_city_change(self, event):
        """
        Handle city selection change
        
        Args:
            event: DOM change event
        """
        # Get the selected city ID
        city_id = event.target.value

        if city_id:
            # Convert to integer
            city_id = int(city_id)

            # Update the selected city in the store
            CityActions.select_city(city_id)

    def fetch_cities(self):
        """Fetch the list of cities from the API"""
        import asyncio
        asyncio.ensure_future(CityActions.fetch_cities())

    def cleanup(self):
        """Clean up the component and unsubscribe from the store"""
        if self.unsubscribe:
            self.unsubscribe()
