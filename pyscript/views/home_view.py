"""
Home view component with city selection and mode selection
"""
import logging

import js
import asyncio
from pyodide.ffi import create_proxy
from ..store.app_store import AppStore
from ..actions.city_actions import CityActions
from ..utils.logging import warn, log

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
        self.cities = dict()
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
        # Update all marker positions when window is resized
        current_lang = js.document.documentElement.lang or "en"

        for city_id, marker in self.city_markers.items():
            # Find the city data
            city = self.cities[city_id]
            city_name = city.get("name_ru" if current_lang == "ru" else "name")
            # Get position from config
            from ..config import CITY_POSITIONS
            if city_id in CITY_POSITIONS:
                position = CITY_POSITIONS.get(city_id)
                # Update marker position
                self._update_marker_position(marker, position)
        # Also update city selection highlight
        self._update_city_selection()

    def _setup_event_handlers(self):
        """Set up event handlers for UI elements"""
        # Existing handlers for modes...

        # Set up language switcher handlers
        lang_buttons = js.document.querySelectorAll('.lang-btn')
        for i in range(lang_buttons.length):
            button = lang_buttons.item(i)
            lang = button.getAttribute('data-lang')

            # Create and store handler
            handler = create_proxy(lambda event, lang=lang: self._on_language_change(event, lang))
            self._handlers[f"lang_{lang}"] = handler

            # Attach handler
            button.addEventListener('click', handler)

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
        bool_need_render = False
        for city in new_cities:
            if city['id'] not in self.cities or self.cities[city['id']] != city:
                bool_need_render = True
                self.cities[city['id']] = city
        if bool_need_render and "home" == state.get("current_view", "home"):
            self._render_city_markers()


        # Update selected city
        new_selected_city_id = state.get("selected_city_id")
        if new_selected_city_id != self.selected_city_id:
            self.cities[new_selected_city_id] = state.get("selected_city_data")
            self.selected_city_id = new_selected_city_id
            self._update_city_selection()
            self._update_city_info()
            self._update_start_button()

    def _render_city_markers(self):
        """Render markers for all cities on the map with dynamic positioning"""

        log("render city markers")
        # Clear existing markers
        self.markers_container.innerHTML = ""
        self.city_markers = {}

        # Import city positions from config
        from ..config import CITY_POSITIONS

        # Get current language
        current_lang = js.document.documentElement.lang or "en"

        # Add markers for each city
        for city_id, city in self.cities.items():
            city_name = city.get("name_ru" if current_lang == "ru" else "name")

            # Skip cities not in our preset positions
            if city_id not in CITY_POSITIONS:
                continue

            # Create marker
            marker = js.document.createElement("div")
            marker.className = "city-marker"
            marker.setAttribute("data-city-id", str(city_id))

            # Set position in percentage based on the map's actual display area
            position = CITY_POSITIONS.get(city_id, {"left": 50, "top": 50})
            
            # Get the actual dimensions of the map
            self._update_marker_position(marker, position)

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

    def _update_marker_position(self, marker, position):
        """
        Update marker position based on the actual map display area
        
        Args:
            marker: The DOM element for the marker
            position: Original position info with 'left' and 'top' in percentages
        """
        map_inner = js.document.querySelector('.map-inner')
        if not map_inner:
            # Fallback to direct percentage if we can't calculate
            marker.style.left = f"{position['left']}%"
            marker.style.top = f"{position['top']}%"
            return
        
        # Get the computed style of the map container
        computed_style = js.window.getComputedStyle(map_inner)
        
        # Get the actual map dimensions (including any padding)
        map_rect = map_inner.getBoundingClientRect()
        container_width = map_rect.width
        container_height = map_rect.height
        
        # Calculate the actual area occupied by the map image
        # This is important because 'background-size: contain' can leave empty space
        orig_width = 2328  # Original SVG width
        orig_height = 1886  # Original SVG height
        aspect_ratio = orig_width / orig_height
        
        if container_width / container_height > aspect_ratio:
            # Map is height-constrained (empty space on sides)
            actual_height = container_height
            actual_width = actual_height * aspect_ratio
            h_offset = (container_width - actual_width) / 2
            v_offset = 0
        else:
            # Map is width-constrained (empty space on top/bottom)
            actual_width = container_width
            actual_height = actual_width / aspect_ratio
            h_offset = 0
            v_offset = (container_height - actual_height) / 2
        
        # Calculate pixel positions relative to the map
        x_percent = position['left']
        y_percent = position['top']
        
        # Adjust for the actual map area within the container
        adjusted_left = h_offset + (x_percent / 100 * actual_width)
        adjusted_top = v_offset + (y_percent / 100 * actual_height)
        
        # Convert back to percentages relative to the container
        final_left = (adjusted_left / container_width) * 100
        final_top = (adjusted_top / container_height) * 100
        
        # Apply the calculated position
        marker.style.left = f"{final_left}%"
        marker.style.top = f"{final_top}%"


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
        selected_city = self.cities[self.selected_city_id]

        # Get current language
        current_lang = js.document.documentElement.lang or "en"
        is_russian = current_lang == "ru"

        # Update info panel
        if selected_city:
            # Use localized name based on language
            city_name = selected_city.get("name_ru" if is_russian else "name", "Unknown City")
            self.info_title.textContent = city_name

            # Create city info content
            content_html = ""

            # Country
            country_label = "Страна:" if is_russian else "Country:"
            country = selected_city.get("country_ru" if is_russian else "country", "Unknown")
            content_html += f"""
            <div class="city-detail">
                <div class="city-detail-label">{country_label}</div>
                <div>{country}</div>
            </div>
            """

            # Founded year
            founded_label = "Основан:" if is_russian else "Founded:"
            founded = selected_city.get("foundation_ru" if is_russian else "foundation", "Unknown")
            content_html += f"""
            <div class="city-detail">
                <div class="city-detail-label">{founded_label}</div>
                <div>{founded}</div>
            </div>
            """

            # Description
            description = selected_city.get("description_ru" if is_russian else "description", "No description available.")
            content_html += f"""
            <div class="city-description">
                {description}
            </div>
            """

            self.info_content.innerHTML = content_html
        else:
            select_message = "Выберите город" if is_russian else "Select a City"
            click_message = "Нажмите на город, чтобы просмотреть информацию." if is_russian else "Click on a city to view information."

            self.info_title.textContent = select_message
            self.info_content.innerHTML = f"<p>{click_message}</p>"

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
        asyncio.ensure_future(CityActions.select_city(city_id))

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
        log(f"selected_mode_id: {mode_id}")

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

        # Trigger simulation view initialization
        from ..dispatch.dispatcher import Dispatcher
        dispatcher = Dispatcher()
        dispatcher.dispatch("NAVIGATE_TO_SIMULATION", {
            "city_id": self.selected_city_id,
            "mode_id": self.selected_mode_id
        })

    def _on_language_change(self, event, lang):
        """Handle language change"""
        # Update active button
        lang_buttons = js.document.querySelectorAll('.lang-btn')
        for i in range(lang_buttons.length):
            button = lang_buttons.item(i)
            if button.getAttribute('data-lang') == lang:
                button.classList.add('active')
            else:
                button.classList.remove('active')
        
        # Set document language
        js.document.documentElement.lang = lang
        
        # Update all translatable elements
        translatable_elements = js.document.querySelectorAll('[data-' + lang + ']')
        for i in range(translatable_elements.length):
            element = translatable_elements.item(i)
            element.textContent = element.getAttribute('data-' + lang)

        current_lang = js.document.documentElement.lang or "en"
        for city_id, marker in self.city_markers.items():
            # Find the corresponding city data
            city_data = self.cities[city_id]
            if city_data:
                # Get the appropriate name based on language
                city_name = city_data.get("name_ru" if current_lang == "ru" else "name", "Unknown")

                # Update the marker label
                label_element = marker.querySelector('.city-marker-label')
                if label_element:
                    label_element.textContent = city_name
        
        # Update city info if a city is selected
        if self.selected_city_id:
            self._update_city_info()



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

