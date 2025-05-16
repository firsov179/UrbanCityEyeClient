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
        self.max_year = 2050
        self._input_handlers = {}

    def initialize(self):
        """Initialize the component and subscribe to store updates"""
        if self.container is None:
            js.console.log(f"Warning: Container {self.container_id} not found in DOM")
            return

        from pyodide.ffi import create_proxy
        self._state_change_handler = create_proxy(self.on_state_change)
        self.unsubscribe = self.store.subscribe(self._state_change_handler)

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

        state = self.store.get_state()
        selected_city_id = state.get("selected_city_id")
        selected_year = state.get("selected_year")
        available_years = state.get("available_years", [])
        loading = state.get("loading", False)

        self.container.innerHTML = ""

        if not selected_city_id:
            message = js.document.createElement("p")
            message.className = "timeline-message"
            message.textContent = "Please select a city to view the timeline."
            self.container.appendChild(message)
            return

        if not available_years or len(available_years) == 0:
            message = js.document.createElement("p")
            message.className = "timeline-message"
            message.textContent = "No timeline data available for this city."
            self.container.appendChild(message)
            return

        sorted_years = sorted(available_years)
        min_year = sorted_years[0]
        max_year = sorted_years[-1]
        self.min_year = min_year
        self.max_year = max_year

        if not selected_year:
            selected_year = sorted_years[0]

        timeline_wrapper = js.document.createElement("div")
        timeline_wrapper.className = "timeline-wrapper"
        timeline_wrapper.style.textAlign = "center"

        controls = js.document.createElement("div")
        controls.className = "timeline-controls"
        controls.style.display = "flex"
        controls.style.justifyContent = "center"
        controls.style.alignItems = "center"
        controls.style.margin = "0 auto"
        controls.style.marginBottom = "10px"
        controls.style.marginTop = "10px"

        prev_btn = js.document.createElement("button")
        prev_btn.className = "timeline-btn prev-btn"
        prev_btn.textContent = "◄"
        prev_btn.title = "Previous Year"
        self._input_handlers['prev'] = create_proxy(self.on_previous_year)
        prev_btn.onclick = self._input_handlers['prev']
        controls.appendChild(prev_btn)

        year_input = js.document.createElement("input")
        year_input.type = "number"
        year_input.min = min_year
        year_input.max = max_year
        year_input.value = selected_year
        year_input.className = "timeline-year-input"
        year_input.style.margin = "0 10px"
        year_input.style.width = "80px"
        year_input.style.textAlign = "center"
        self._input_handlers['year'] = create_proxy(self.on_year_input_change)
        year_input.onchange = self._input_handlers['year']
        controls.appendChild(year_input)

        next_btn = js.document.createElement("button")
        next_btn.className = "timeline-btn next-btn"
        next_btn.textContent = "►"
        next_btn.title = "Next Year"
        self._input_handlers['next'] = create_proxy(self.on_next_year)
        next_btn.onclick = self._input_handlers['next']
        controls.appendChild(next_btn)

        timeline_wrapper.appendChild(controls)

        slider_container = js.document.createElement("div")
        slider_container.className = "timeline-slider-container"
        slider_container.style.width = "70%"
        slider_container.style.margin = "0 auto"
        slider_container.style.position = "relative"

        slider = js.document.createElement("input")
        slider.type = "range"
        slider.min = min_year
        slider.max = max_year
        slider.step = 1
        slider.value = selected_year
        slider.className = "timeline-slider"
        slider.style.width = "100%"
        self._input_handlers['slider'] = create_proxy(self.on_slider_change)
        slider.oninput = self._input_handlers['slider']
        slider_container.appendChild(slider)

        range_labels = js.document.createElement("div")
        range_labels.className = "timeline-range-labels"
        range_labels.style.display = "flex"
        range_labels.style.justifyContent = "space-between"
        range_labels.style.marginTop = "5px"

        min_label = js.document.createElement("span")
        min_label.textContent = str(min_year)
        range_labels.appendChild(min_label)

        max_label = js.document.createElement("span")
        max_label.textContent = str(max_year)
        range_labels.appendChild(max_label)

        slider_container.appendChild(range_labels)

        timeline_wrapper.appendChild(slider_container)

        self.container.appendChild(timeline_wrapper)

        if loading:
            loading_elem = js.document.createElement("div")
            loading_elem.className = "timeline-loading"
            loading_elem.textContent = "Loading..."
            loading_elem.style.textAlign = "center"
            loading_elem.style.marginTop = "10px"
            timeline_wrapper.appendChild(loading_elem)


    def on_year_input_change(self, event):
        """Handle year input change"""
        try:
            year = int(event.target.value)

            if year < self.min_year:
                year = self.min_year
                event.target.value = self.min_year
            elif year > self.max_year:
                year = self.max_year
                event.target.value = self.max_year

            state = self.store.get_state()
            city_id = state.get("selected_city_id")

            if city_id:
                CityActions.select_year(city_id, year)
        except ValueError:
            state = self.store.get_state()
            current_year = state.get("selected_year")
            if current_year:
                event.target.value = current_year

    def on_slider_change(self, event):
        """Handle slider change"""
        try:
            year = int(event.target.value)

            state = self.store.get_state()
            city_id = state.get("selected_city_id")

            if city_id:
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
            SimulationActions.stop_timeline_animation()
        else:
            asyncio.ensure_future(SimulationActions.start_timeline_animation())

    def cleanup(self):
        """Clean up the component and unsubscribe from the store"""
        if self.unsubscribe:
            self.unsubscribe()

        for key, handler in self._input_handlers.items():
            handler.destroy()

        if self.animation_active:
            SimulationActions.stop_timeline_animation()
