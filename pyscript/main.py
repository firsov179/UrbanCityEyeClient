"""
Main entry point for the PyScript City Infrastructure Evolution application.
Initializes all components and sets up the application.
"""
import js
import sys
import traceback
import asyncio
from pyodide.ffi import create_proxy
from pyscript.store.app_store import AppStore
from pyscript.dispatch.dispatcher import Dispatcher
from pyscript.views.city_selector import CitySelector
from pyscript.views.timeline import Timeline
from pyscript.views.map_view import MapView
from pyscript.views.info_panel import InfoPanel
from pyscript.actions.city_actions import CityActions
from pyscript.actions.simulation_actions import SimulationActions
from pyscript.actions.geo_actions import GeoActions
from pyscript.config import API_BASE_URL, MAP_DEFAULT_CENTER, MAP_DEFAULT_ZOOM, DEFAULT_CITY_ID, DEFAULT_YEAR

# Global variables to hold view instances
city_selector = None
timeline = None
map_view = None
info_panel = None
store = None


# Глобальный обработчик исключений
def global_exception_handler(exctype, value, tb):
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    print(f"Uncaught Python exception: {error_msg}")
    js.console.error(f"Python Error: {error_msg}")

    # Отображение ошибки на странице
    try:
        error_div = js.document.createElement("div")
        error_div.className = "python-error"
        error_div.style.color = "red"
        error_div.style.padding = "10px"
        error_div.style.margin = "10px"
        error_div.style.border = "1px solid red"
        error_div.style.backgroundColor = "#ffeeee"
        error_div.innerHTML = f"<h3>Python Error</h3><pre>{error_msg}</pre>"
        js.document.body.appendChild(error_div)
    except Exception as e:
        print(f"Failed to display error message: {e}")


sys.excepthook = global_exception_handler


async def initialize_app():
    """Initialize the application and all its components"""
    global city_selector, timeline, map_view, info_panel, store

    print("Initializing City Infrastructure Evolution Application")

    # Initialize the store and dispatcher
    store = AppStore()
    dispatcher = Dispatcher()

    # Create and initialize view components
    city_selector = CitySelector()
    timeline = Timeline()
    map_view = MapView()
    info_panel = InfoPanel()

    # Initialize each component
    city_selector.initialize()
    timeline.initialize()
    map_view.initialize()
    info_panel.initialize()

    # Register keyboard event listeners
    register_keyboard_events()

    # Add window resize listener
    js.window.addEventListener("resize", create_proxy(on_window_resize))

    # Initialize data
    await load_initial_data()

    print(f"Application initialized. API endpoint: {API_BASE_URL}")


def register_keyboard_events():
    """Register keyboard event listeners for app shortcuts"""

    def handle_key_press(event):
        """Handle keyboard events"""
        key = event.key.lower()

        # Arrow keys for timeline navigation
        if key == "arrowright":
            SimulationActions.jump_to_next_year()
        elif key == "arrowleft":
            SimulationActions.jump_to_previous_year()

        # Spacebar to toggle animation
        elif key == " " or key == "spacebar":
            # Get current animation state
            state = store.get_state()
            animation_active = state.get("animation_active", False)

            if animation_active:
                SimulationActions.stop_timeline_animation()
            else:
                asyncio.ensure_future(SimulationActions.start_timeline_animation())

        # Escape key to close info panel
        elif key == "escape":
            GeoActions.toggle_info_panel(False)

    # Create a proxy function for the event handler
    handle_key_press_proxy = create_proxy(handle_key_press)

    # Register the event listener
    js.document.addEventListener("keydown", handle_key_press_proxy)


def on_window_resize(event):
    """Handle window resize event"""
    # Update layout if needed
    if map_view and map_view.map:
        # Force Leaflet to update its size
        map_view.map.invalidateSize()


async def load_initial_data():
    """Load initial data for the application"""
    # Fetch the list of cities
    cities = await CityActions.fetch_cities()

    if cities and len(cities) > 0:
        # If DEFAULT_CITY_ID is defined, select that city, otherwise select the first city
        city_id = DEFAULT_CITY_ID
        if not any(city["id"] == city_id for city in cities):
            city_id = cities[0]["id"]

        # Select the city
        CityActions.select_city(city_id)

        # The rest of the data loading is handled by the CityActions.select_city function
        # which triggers the loading of years, simulations, and geo objects
    else:
        print("No cities available. Please check your database connection.")


def handle_errors():
    """Set up global error handling"""

    def on_error(event):
        """Handle uncaught errors"""
        error_msg = f"An error occurred: {event.message}"
        print(error_msg)

        # Dispatch error to store
        dispatcher = Dispatcher()
        dispatcher.dispatch("GLOBAL_ERROR", {"message": error_msg})

        # Prevent default browser error handling
        event.preventDefault()
        return True

    # Create a proxy function for the error handler
    on_error_proxy = create_proxy(on_error)

    # Register error event handlers
    js.window.addEventListener("error", on_error_proxy)
    js.window.addEventListener("unhandledrejection", on_error_proxy)


def cleanup():
    """Clean up resources when the application is unloaded"""
    if city_selector:
        city_selector.cleanup()

    if timeline:
        timeline.cleanup()

    if map_view:
        map_view.cleanup()

    if info_panel:
        info_panel.cleanup()

    print("Application cleanup completed")


# Entry point
async def main():
    """Main entry point"""
    # Set up error handling
    handle_errors()

    # Initialize the application
    await initialize_app()

    # Register cleanup function to be called on window unload
    js.window.addEventListener("unload", create_proxy(cleanup))

    print("City Infrastructure Evolution Application is ready")


# Execute the main function
asyncio.ensure_future(main())
