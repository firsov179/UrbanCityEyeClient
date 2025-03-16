"""
Simulation view component for the simulation screen
"""
import js
from pyodide.ffi import create_proxy
from ..store.app_store import AppStore
from ..views.map_view import MapView
from ..views.timeline import Timeline
from ..views.info_panel import InfoPanel
from ..utils.logging import *
from ..actions.city_actions import CityActions
import asyncio

class SimulationView:
    """Simulation view component"""

    def __init__(self, screen_id="simulation-screen", back_button_id="back-to-home"):
        """
        Initialize the simulation view

        Args:
            screen_id: ID of the screen container
            back_button_id: ID of the back button
        """
        self.screen_id = screen_id
        self.screen = js.document.getElementById(screen_id)
        self.back_button_id = back_button_id
        self.back_button = js.document.getElementById(back_button_id)

        self.store = AppStore()
        self.map_view = None
        self.timeline = None
        self.info_panel = None

        self.initialized = False
        self.unsubscribe = None
        self._handlers = {}

    def initialize(self):
        """Initialize the component and its sub-components"""
        if not self.screen:
            warn(f"Warning: Screen element {self.screen_id} not found in the DOM")
            return

        # Set up back button handler
        back_handler = create_proxy(self._on_back_button)
        self._handlers["back"] = back_handler
        self.back_button.addEventListener("click", back_handler)

        # Subscribe to store changes
        self._state_change_handler = create_proxy(self.on_state_change)
        self.unsubscribe = self.store.subscribe(self._state_change_handler)

        # Initialize sub-components
        self.map_view = MapView()
        self.timeline = Timeline()
        self.info_panel = InfoPanel()

        # Mark as initialized
        self.initialized = True
        self._initialization_in_progress = False
        self.year = None
        self.city_id = None
        self.mode_id = None

        log("SimulationView initialized")

    def on_state_change(self, state):
        """
        Handle state changes from the store

        Args:
            state: Current application state
        """
        if "simulation" != state.get("current_view", "home"):
            return

        # Check if we should navigate to simulation view
        navigate_to_simulation = state.get("navigate_to_simulation", False)

        if navigate_to_simulation and self.initialized:
            log(f"Processing navigation to simulation: {navigate_to_simulation}")

            # Сначала сбрасываем флаг навигации, чтобы предотвратить повторную инициализацию
            from ..dispatch.dispatcher import Dispatcher
            dispatcher = Dispatcher()
            dispatcher.dispatch("RESET_NAVIGATION", None)

            # Затем инициализируем симуляцию
            asyncio.ensure_future(self._initialize_simulation(navigate_to_simulation))

        if self.year != state.get("selected_year", self.year):
            self.year = state.get("selected_year", self.year)
            asyncio.ensure_future(CityActions.select_city_simulation(self.city_id, self.year, self.mode_id))

    async def _initialize_simulation(self, navigation_data):
        """
        Initialize the simulation with the given data

        Args:
            navigation_data: Data for initializing the simulation
        """
        log(f"Initializing simulation with data: {navigation_data}")

        # Static variable to prevent re-initialization
        if not self._initialization_in_progress:
            self._initialization_in_progress = True
            log("_initialization_in_progress = True")
        else:
            log("Initialization already in progress, skipping")
            return

        try:
            # Extract city_id and mode_id
            self.city_id = navigation_data.get("city_id")
            self.mode_id = navigation_data.get("mode_id")

            if not self.city_id:
                error("No city_id provided for simulation initialization")
                return

            if not self.mode_id:
                error("No mode_id provided for simulation initialization")
                return

            self._update_mode_ui(self.mode_id)

            # Здесь загружаем полные данные для симуляции
            from ..actions.city_actions import CityActions

            available_years = await CityActions.fetch_available_years(self.city_id)
            self.year = available_years[0] if available_years is not None else 1500

            await CityActions.select_city_simulation(self.city_id, self.year, self.mode_id)

            # Initialize sub-components if they haven't been initialized
            if self.map_view and not getattr(self.map_view, '_initialized', False):
                log("Initializing MapView")
                self.map_view.initialize()

            if self.timeline and not getattr(self.timeline, '_initialized', False):
                log("Initializing Timeline")
                self.timeline.initialize()

            if self.info_panel and not getattr(self.info_panel, '_initialized', False):
                log("Initializing InfoPanel")
                self.info_panel.initialize()

            log(f"Simulation initialization complete for city_id: { self.city_id}, mode_id: {self.mode_id}")
        finally:
            # Clear initialization flag
            self._initialization_in_progress = False
            log("_initialization_in_progress = False")

    def _update_mode_ui(self, mode_id):
        """
        Update UI to reflect the selected mode

        Args:
            mode_id: ID of the selected mode
        """
        # This could include updating titles, colors, or other UI elements
        # based on the selected mode

        # Example: Update the info panel title
        if self.info_panel:
            title_elem = js.document.querySelector(f"#{self.info_panel.panel_id} > h2")
            if title_elem:
                if mode_id == 1:
                    title_elem.textContent = "Transport Infrastructure"
                elif mode_id == 2:
                    title_elem.textContent = "Housing Development"
                else:
                    title_elem.textContent = "Information"

    def _on_back_button(self, event):
        """Handle back button click"""
        log("Back button clicked, returning to home screen")

        # Hide simulation screen
        self.screen.classList.remove("active")

        # Show home screen
        home_screen = js.document.getElementById("home-screen")
        home_screen.classList.add("active")

        from ..dispatch.dispatcher import Dispatcher
        dispatcher = Dispatcher()
        dispatcher.dispatch("CLEAR_SELECTION", None)
        dispatcher.dispatch("NAVIGATE_TO_HOME")

    def show(self):
        """Show this view"""
        self.screen.classList.add("active")

        # Force map to refresh if needed
        if self.map_view and self.map_view.map:
            self.map_view.map.invalidateSize()

    def hide(self):
        """Hide this view"""
        self.screen.classList.remove("active")

    def cleanup(self):
        """Clean up resources when the component is destroyed"""
        log("Cleaning up SimulationView resources")

        if self.unsubscribe:
            try:
                self.unsubscribe()
                self.unsubscribe = None
            except Exception as e:
                error(f"Error during unsubscribe: {e}")

        # Clean up event handlers
        for handler_name, handler in self._handlers.items():
            try:
                handler.destroy()
            except Exception as e:
                error(f"Error destroying handler {handler_name}: {e}")

        if hasattr(self, '_state_change_handler'):
            try:
                self._state_change_handler.destroy()
            except Exception as e:
                error(f"Error destroying state change handler: {e}")

        # Clean up sub-components
        if self.map_view:
            try:
                self.map_view.cleanup()
            except Exception as e:
                error(f"Error cleaning up MapView: {e}")

        if self.timeline:
            try:
                self.timeline.cleanup()
            except Exception as e:
                error(f"Error cleaning up Timeline: {e}")

        if self.info_panel:
            try:
                self.info_panel.cleanup()
            except Exception as e:
                error(f"Error cleaning up InfoPanel: {e}")

        log("SimulationView cleanup completed")
