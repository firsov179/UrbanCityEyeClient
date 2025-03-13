"""
Home view component with city selection and mode selection
"""
import js
from pyodide.ffi import create_proxy
from ..store.app_store import AppStore
from ..actions.city_actions import CityActions
from ..utils.logging import warn

class HomeView:
    """Home view with city selection and mode selection"""

    def __init__(self,
                 screen_id="home-screen",
                 markers_container_id="city-markers-container",
                 info_title_id="city-info-title",
                 info_content_id="city-info-content",
                 start_btn_id="start-simulation"):
        """
        Initialize the home view

        Args:
            screen_id: ID of the screen container
            markers_container_id: ID of the city markers container
            info_title_id: ID of the city info title element
            info_content_id: ID of the city info content element
            start_btn_id: ID of the start simulation button
        """
        self.screen_id = screen_id
        self.screen = js.document.getElementById(screen_id)
        self.markers_container_id = markers_container_id
        self.markers_container = None
        self.info_title_id = info_title_id
        self.info_title = js.document.getElementById(info_title_id)
        self.info_content_id = info_content_id
        self.info_content = js.document.getElementById(info_content_id)
        self.start_btn_id = start_btn_id
        self.start_btn = js.document.getElementById(start_btn_id)

        self.store = AppStore()
        self.cities = []
        self.selected_city_id = None
        self.selected_mode_id = 1  # Default: Transport Infrastructure

        self.city_markers = {}
        self.unsubscribe = None
        self._handlers = {}

    def initialize(self):
        """Initialize the component and load cities"""
        if not self.screen or not self.markers_container:
            warn(f"Warning: Required elements not found in the DOM")

        self.markers_container = js.document.getElementById(self.markers_container_id)
        if not self.markers_container:
            print(f"Warning: Markers container {self.markers_container_id} not found in the DOM")
            return

        # Set up event handlers
        self._setup_event_handlers()

        # Add window resize handler
        self._resize_handler = create_proxy(self._on_window_resize)
        js.window.addEventListener("resize", self._resize_handler)

        # Subscribe to store changes
        self._state_change_handler = create_proxy(self.on_state_change)
        self.unsubscribe = self.store.subscribe(self._state_change_handler)

        # Fetch cities
        self._fetch_cities()

    def _on_window_resize(self, event):
        """Handle window resize event"""
        # Rerenders the city markers to adapt to new window size
        self._update_city_selection()

    def _setup_event_handlers(self):
        """Set up event handlers for UI elements"""
        # Set up mode selection handlers
        mode_options = self.screen.querySelectorAll('.mode-option')
        for i in range(mode_options.length):
            option = mode_options.item(i)
            mode_id = i + 1  # Mode IDs start from 1

            # Create and store handler
            handler = create_proxy(lambda event, mode_id=mode_id: self._on_mode_select(event, mode_id))
            self._handlers[f"mode_{mode_id}"] = handler

            # Attach handler
            option.addEventListener('click', handler)

        # Set up start simulation button handler
        start_handler = create_proxy(self._on_start_simulation)
        self._handlers["start"] = start_handler
        self.start_btn.addEventListener('click', start_handler)

    def _fetch_cities(self):
        """Fetch cities from the API"""
        import asyncio
        asyncio.ensure_future(CityActions.fetch_cities())

    def on_state_change(self, state):
        """
        Handle state changes from the store

        Args:
            state: Current application state
        """
        # Update cities if they've changed
        new_cities = state.get("cities", [])
        if new_cities != self.cities:
            self.cities = new_cities
            self._render_city_markers()

        # Update selected city
        new_selected_city_id = state.get("selected_city_id")
        if new_selected_city_id != self.selected_city_id:
            self.selected_city_id = new_selected_city_id
            self._update_city_selection()
            self._update_city_info()
            self._update_start_button()

    def _render_city_markers(self):
        """Render markers for all cities on the map"""
        # Clear existing markers
        self.markers_container.innerHTML = ""
        self.city_markers = {}

        # Import city positions from config
        from ..config import CITY_POSITIONS

        # Add markers for each city
        for city in self.cities:
            city_id = city.get("id")
            city_name = city.get("name")

            # Skip cities not in our preset positions
            if city_name not in CITY_POSITIONS:
                continue

            # Create marker
            marker = js.document.createElement("div")
            marker.className = "city-marker"
            marker.setAttribute("data-city-id", str(city_id))

            # Set position in percentage
            position = CITY_POSITIONS.get(city_name, {"left": 50, "top": 50})
            marker.style.left = f"{position['left']}%"
            marker.style.top = f"{position['top']}%"

            # Create label
            label = js.document.createElement("div")
            label.className = "city-marker-label"
            label.textContent = city_name

            # Add click handler
            handler = create_proxy(lambda event, city_id=city_id: self._on_city_click(event, city_id))
            self._handlers[f"city_{city_id}"] = handler
            marker.addEventListener("click", handler)

            # Add elements to DOM
            marker.appendChild(label)
            self.markers_container.appendChild(marker)

            # Add marker to map
            if self.selected_city_id == city_id:
                marker.classList.add("active")

            # Save reference
            self.city_markers[city_id] = marker

    def _update_city_selection(self):
        """Update visual selection of cities on the map"""
        # Remove active class from all markers
        for marker_id, marker in self.city_markers.items():
            marker.classList.remove("active")

        # Add active class to selected marker
        if self.selected_city_id in self.city_markers:
            self.city_markers[self.selected_city_id].classList.add("active")

    def _update_city_info(self):
        """Update city information panel"""
        # Find the selected city
        selected_city = None
        for city in self.cities:
            if city.get("id") == self.selected_city_id:
                selected_city = city
                break

        # Update info panel
        if selected_city:
            self.info_title.textContent = selected_city.get("name", "Unknown City")

            # Create city info content
            content_html = ""

            # Country
            country = selected_city.get("country", "Unknown")
            content_html += f"""
            <div class="city-detail">
                <div class="city-detail-label">Country:</div>
                <div>{country}</div>
            </div>
            """

            # Founded year
            founded = selected_city.get("founded", "Unknown")
            content_html += f"""
            <div class="city-detail">
                <div class="city-detail-label">Founded:</div>
                <div>{founded}</div>
            </div>
            """

            # Description
            description = selected_city.get("description", "No description available.")
            content_html += f"""
            <div class="city-description">
                {description}
            </div>
            """

            self.info_content.innerHTML = content_html
        else:
            self.info_title.textContent = "Select a City"
            self.info_content.innerHTML = "<p>Click on a city to view information.</p>"

    def _update_start_button(self):
        """Update start simulation button state"""
        if self.selected_city_id:
            self.start_btn.disabled = False
        else:
            self.start_btn.disabled = True

    def _on_city_click(self, event, city_id):
        """
        Handle city marker click

        Args:
            event: DOM event
            city_id: ID of the clicked city
        """
        # Только выбираем город без загрузки дополнительных данных
        CityActions.select_city(city_id)

    def _on_mode_select(self, event, mode_id):
        """
        Handle mode selection

        Args:
            event: DOM event
            mode_id: ID of the selected mode
        """
        # Update mode in UI
        mode_options = self.screen.querySelectorAll('.mode-option')
        for i in range(mode_options.length):
            option = mode_options.item(i)
            if i + 1 == mode_id:
                option.classList.add("active")
            else:
                option.classList.remove("active")

        # Update selected mode
        self.selected_mode_id = mode_id

        # Update store (только обновляем режим, не вызываем загрузку данных)
        from ..dispatch.dispatcher import Dispatcher
        dispatcher = Dispatcher()
        dispatcher.dispatch("SELECT_MODE_HOME", mode_id)  # Используем другое действие

    def _on_start_simulation(self, event):
        """Handle start simulation button click"""
        if not self.selected_city_id:
            return

        # Switch to simulation screen
        self.screen.classList.remove("active")
        simulation_screen = js.document.getElementById("simulation-screen")
        simulation_screen.classList.add("active")

        # Здесь загружаем полные данные для симуляции
        from ..actions.city_actions import CityActions
        CityActions.select_city_simulation(self.selected_city_id)

        # Trigger simulation view initialization
        from ..dispatch.dispatcher import Dispatcher
        dispatcher = Dispatcher()
        dispatcher.dispatch("NAVIGATE_TO_SIMULATION", {
            "city_id": self.selected_city_id,
            "mode_id": self.selected_mode_id
        })


    def show(self):
        """Show this view"""
        self.screen.classList.add("active")

    def hide(self):
        """Hide this view"""
        self.screen.classList.remove("active")

    def cleanup(self):
        """Clean up resources when the component is destroyed"""
        if self.unsubscribe:
            self.unsubscribe()

        # Clean up event handlers
        for handler_name, handler in self._handlers.items():
            handler.destroy()

        if hasattr(self, '_state_change_handler'):
            self._state_change_handler.destroy()

        if hasattr(self, '_resize_handler'):
            js.window.removeEventListener("resize", self._resize_handler)
            self._resize_handler.destroy()

