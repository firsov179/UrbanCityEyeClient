"""
Main entry point for the PyScript Urban City Eye application.
Initializes all components and sets up the application.
"""
import js
import sys
import traceback
import asyncio
from pyodide.ffi import create_proxy
from pyscript.store.app_store import AppStore
from pyscript.dispatch.dispatcher import Dispatcher
from pyscript.views.timeline import Timeline
from pyscript.views.map_view import MapView
from pyscript.views.info_panel import InfoPanel
from pyscript.views.home_view import HomeView
from pyscript.views.simulation_view import SimulationView
from pyscript.actions.city_actions import CityActions
from pyscript.actions.simulation_actions import SimulationActions
from pyscript.actions.geo_actions import GeoActions
from pyscript.config import API_BASE_URL, MAP_DEFAULT_CENTER, MAP_DEFAULT_ZOOM
from pyscript.utils.logging import *

timeline = None
map_view = None
info_panel = None
home_view = None
simulation_view = None
store = None
app_initialized = False


def global_exception_handler(exctype, value, tb):
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    error("Uncaught Python exception:", error_msg)

    try:
        if js:
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
        error(f"Failed to display error message: {e}")


sys.excepthook = global_exception_handler


async def initialize_app():
    """Initialize the application and all its components"""
    global timeline, map_view, info_panel, home_view, simulation_view, store, app_initialized

    if app_initialized:
        log("App already initialized, skipping initialization")
        return

    log("Initializing Urban City Eye Application")

    app_initialized = True

    store = AppStore()
    dispatcher = Dispatcher()

    home_view = HomeView()
    simulation_view = SimulationView()

    timeline_container = js.document.getElementById("timeline-container")

    if timeline_container:
        timeline = Timeline()
        timeline.initialize()


    # Инициализация остальных компонентов
    home_view.initialize()
    simulation_view.initialize()

    # Register keyboard event listeners
    register_keyboard_events()

    # Add window resize listener
    js.window.addEventListener("resize", create_proxy(on_window_resize))
    await load_initial_data()

    # Показываем начальный экран
    show_home_view()

    log(f"Application initialized. API endpoint: {API_BASE_URL}")

def show_home_view():
    """Show the home view"""
    home_screen = js.document.getElementById("home-screen")
    simulation_screen = js.document.getElementById("simulation-screen")

    if home_screen:
        home_screen.classList.add("active")
    if simulation_screen:
        simulation_screen.classList.remove("active")


def show_simulation_view():
    """Show the simulation view"""
    home_screen = js.document.getElementById("home-screen")
    simulation_screen = js.document.getElementById("simulation-screen")

    if home_screen:
        home_screen.classList.remove("active")
    if simulation_screen:
        simulation_screen.classList.add("active")

    if map_view and map_view.map:
        map_view.map.invalidateSize()

def register_keyboard_events():
    """Register keyboard event listeners for app shortcuts"""

    def handle_key_press(event):
        """Handle keyboard events"""
        state = store.get_state()
        current_view = state.get("current_view", "home")

        key = event.key.lower()

        if key == "arrowright":
            SimulationActions.jump_to_next_year()
        elif key == "arrowleft":
            SimulationActions.jump_to_previous_year()

        elif key == " " or key == "spacebar":
            animation_active = state.get("animation_active", False)

            if isinstance(animation_active, dict):
                animation_active = animation_active.get("active", False)

            if animation_active:
                SimulationActions.stop_timeline_animation()
            else:
                asyncio.ensure_future(SimulationActions.start_timeline_animation())

    handle_key_press_proxy = create_proxy(handle_key_press)

    js.document.addEventListener("keydown", handle_key_press_proxy)


def on_window_resize(event):
    """Handle window resize event"""
    state = store.get_state()
    current_view = state.get("current_view", "home")

    if current_view == "simulation":
        if map_view and map_view.map:
            map_view.map.invalidateSize()


async def load_initial_data():
    """Load initial data for the application"""
    try:
        cities = await CityActions.fetch_cities()

        if cities and len(cities) > 0:
            log(f"Loaded {len(cities)} cities for the home view")
        else:
            log("No cities available. Please check your database connection.")
    except Exception as e:
        error(f"Error loading initial data: {e}")
        import traceback
        error(traceback.format_exc())



def handle_errors():
    """Set up global error handling"""
    def on_error(event):
        """Handle uncaught errors"""
        error_msg = f"An error occurred: {event.message}"
        log(error_msg)

        dispatcher = Dispatcher()
        dispatcher.dispatch("GLOBAL_ERROR", {"message": error_msg})

        event.preventDefault()
        return True

    on_error_proxy = create_proxy(on_error)

    js.window.addEventListener("error", on_error_proxy)
    js.window.addEventListener("unhandledrejection", on_error_proxy)


def cleanup():
    if home_view:
        home_view.cleanup()

    if simulation_view:
        simulation_view.cleanup()


    if timeline:
        timeline.cleanup()

    if map_view:
        map_view.cleanup()

    if info_panel:
        info_panel.cleanup()

    log("Application cleanup completed")


async def main():
    """Main entry point"""
    try:
        handle_errors()

        await initialize_app()

        js.window.addEventListener("unload", create_proxy(cleanup))

        log("Urban City Eye Application is ready")
    except Exception as e:
        log(f"Error in main: {str(e)}")


if not app_initialized:
    asyncio.ensure_future(main())

