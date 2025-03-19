"""
Timeline component for visualizing and navigating through years
"""
import js
from pyodide.ffi import create_proxy
from ..store.app_store import AppStore
from ..actions.city_actions import CityActions
from ..actions.simulation_actions import SimulationActions

class Timeline:
    """Timeline component for visualizing and selecting years"""

    def __init__(self, container_id="timeline-container"):
        """
        Initialize the timeline component

        Args:
            container_id: ID of the HTML container element
        """
        self.container_id = container_id
        self.container = js.document.getElementById(container_id)
        self.store = AppStore()
        self.unsubscribe = None
        self.animation_active = False
        self.min_year = 1500
        self.max_year = 2020
        self._input_handlers = {}

    def initialize(self):
        """Initialize the component and subscribe to store updates"""
        if self.container is None:
            js.console.log(f"Warning: Container {self.container_id} not found in DOM")
            return

        # Subscribe to store changes
        from pyodide.ffi import create_proxy
        self._state_change_handler = create_proxy(self.on_state_change)
        self.unsubscribe = self.store.subscribe(self._state_change_handler)

        # Initial render
        self.render()

    def on_state_change(self, state):
        """
        Handle state changes from the store

        Args:
            state: Current application state
        """
        self.animation_active = state.get("animation_active", False)
        if isinstance(self.animation_active, dict):
            self.animation_active = self.animation_active.get("active", False)

        # Update available years
        available_years = state.get("available_years", [])
        if available_years:
            sorted_years = sorted(available_years)
            if len(sorted_years) > 0:
                self.min_year = sorted_years[0]
                self.max_year = sorted_years[-1]

        self.render()

    def render(self):
        """Render the timeline component"""
        if self.container is None:
            return

        # Get the current state
        state = self.store.get_state()
        selected_city_id = state.get("selected_city_id")
        selected_year = state.get("selected_year")
        available_years = state.get("available_years", [])
        loading = state.get("loading", False)

        # Clear previous content
        self.container.innerHTML = ""

        # If no city is selected, show a message
        if not selected_city_id:
            message = js.document.createElement("p")
            message.className = "timeline-message"
            message.textContent = "Please select a city to view the timeline."
            self.container.appendChild(message)
            return

        # If no years are available, show a message
        if not available_years or len(available_years) == 0:
            message = js.document.createElement("p")
            message.className = "timeline-message"
            message.textContent = "No timeline data available for this city."
            self.container.appendChild(message)
            return

        # Sort years
        sorted_years = sorted(available_years)
        min_year = sorted_years[0]
        max_year = sorted_years[-1]
        self.min_year = min_year
        self.max_year = max_year

        # Default selected year if none is set
        if not selected_year:
            selected_year = sorted_years[0]

        # Create controls container
        controls = js.document.createElement("div")
        controls.className = "timeline-controls"

        # Add previous button
        prev_btn = js.document.createElement("button")
        prev_btn.className = "timeline-btn prev-btn"
        prev_btn.textContent = "◄"
        prev_btn.title = "Previous Year"
        self._input_handlers['prev'] = create_proxy(self.on_previous_year)
        prev_btn.onclick = self._input_handlers['prev']
        controls.appendChild(prev_btn)

        # Add play/pause button
        play_btn = js.document.createElement("button")
        play_btn.className = f"timeline-btn play-btn {'pause-btn' if self.animation_active else ''}"
        play_btn.textContent = "⏵︎" if not self.animation_active else "⏸︎"
        play_btn.title = "Play/Pause Animation"
        self._input_handlers['play'] = create_proxy(self.toggle_animation)
        play_btn.onclick = self._input_handlers['play']
        controls.appendChild(play_btn)

        # Add next button
        next_btn = js.document.createElement("button")
        next_btn.className = "timeline-btn next-btn"
        next_btn.textContent = "►"
        next_btn.title = "Next Year"
        self._input_handlers['next'] = create_proxy(self.on_next_year)
        next_btn.onclick = self._input_handlers['next']
        controls.appendChild(next_btn)

        # Add controls to container
        self.container.appendChild(controls)

        # Create year input
        year_input = js.document.createElement("input")
        year_input.type = "number"
        year_input.min = min_year
        year_input.max = max_year
        year_input.value = selected_year
        year_input.className = "timeline-year-input"
        self._input_handlers['year'] = create_proxy(self.on_year_input_change)
        year_input.onchange = self._input_handlers['year']
        self.container.appendChild(year_input)

        # Create slider container
        slider_container = js.document.createElement("div")
        slider_container.className = "timeline-slider-container"

        # Create slider
        slider = js.document.createElement("input")
        slider.type = "range"
        slider.min = min_year
        slider.max = max_year
        slider.step = 1
        slider.value = selected_year
        slider.className = "timeline-slider"
        self._input_handlers['slider'] = create_proxy(self.on_slider_change)
        slider.oninput = self._input_handlers['slider']
        slider_container.appendChild(slider)

        # Create range labels
        range_labels = js.document.createElement("div")
        range_labels.className = "timeline-range-labels"

        # Add min year label
        min_label = js.document.createElement("span")
        min_label.textContent = str(min_year)
        range_labels.appendChild(min_label)

        # Add max year label
        max_label = js.document.createElement("span")
        max_label.textContent = str(max_year)
        range_labels.appendChild(max_label)

        slider_container.appendChild(range_labels)

        # Add slider container to main container
        self.container.appendChild(slider_container)

        # Add loading indicator if needed
        if loading:
            loading_elem = js.document.createElement("div")
            loading_elem.className = "timeline-loading"
            loading_elem.textContent = "Loading..."
            self.container.appendChild(loading_elem)

    def on_year_input_change(self, event):
        """Handle year input change"""
        try:
            year = int(event.target.value)

            # Validate year range
            if year < self.min_year:
                year = self.min_year
                event.target.value = self.min_year
            elif year > self.max_year:
                year = self.max_year
                event.target.value = self.max_year

            # Get the current city
            state = self.store.get_state()
            city_id = state.get("selected_city_id")

            if city_id:
                # Select the year
                CityActions.select_year(city_id, year)
        except ValueError:
            # Reset to current year if input is invalid
            state = self.store.get_state()
            current_year = state.get("selected_year")
            if current_year:
                event.target.value = current_year

    def on_slider_change(self, event):
        """Handle slider change"""
        try:
            year = int(event.target.value)

            # Get the current city
            state = self.store.get_state()
            city_id = state.get("selected_city_id")

            if city_id:
                # Select the year
                CityActions.select_year(city_id, year)
        except ValueError:
            pass

    def on_previous_year(self, event):
        """Handle previous year button click"""
        SimulationActions.jump_to_previous_year()

    def on_next_year(self, event):
        """Handle next year button click"""
        SimulationActions.jump_to_next_year()

    def toggle_animation(self, event):
        """Toggle timeline animation play/pause"""
        import asyncio

        if self.animation_active:
            # Stop animation
            SimulationActions.stop_timeline_animation()
        else:
            # Start animation
            asyncio.ensure_future(SimulationActions.start_timeline_animation())

    def cleanup(self):
        """Clean up the component and unsubscribe from the store"""
        if self.unsubscribe:
            self.unsubscribe()

        # Clean up event handlers
        for key, handler in self._input_handlers.items():
            handler.destroy()

        # Ensure animation is stopped
        if self.animation_active:
            SimulationActions.stop_timeline_animation()
