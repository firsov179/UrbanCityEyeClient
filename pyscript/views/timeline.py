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

    def initialize(self):
        """Initialize the component and subscribe to store updates"""
        if self.container is None:
            print(f"Warning: Container {self.container_id} not found in the DOM")
            return

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
        self.animation_active = state.get("animation_active", False)
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

        # Clear the container
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

        # Create the timeline container
        timeline_elem = js.document.createElement("div")
        timeline_elem.className = "timeline"

        # Add timeline controls
        controls = js.document.createElement("div")
        controls.className = "timeline-controls"

        # Add previous button
        prev_btn = js.document.createElement("button")
        prev_btn.className = "timeline-btn prev-btn"
        prev_btn.textContent = "◄"
        prev_btn.title = "Previous Year"
        prev_btn.onclick = create_proxy(self.on_previous_year)
        controls.appendChild(prev_btn)

        # Add play/pause button
        play_btn = js.document.createElement("button")
        play_btn.className = f"timeline-btn play-btn {'pause-btn' if self.animation_active else ''}"
        play_btn.textContent = "⏵︎" if not self.animation_active else "⏸︎"
        play_btn.title = "Play/Pause Animation"
        play_btn.onclick = create_proxy(self.toggle_animation)
        controls.appendChild(play_btn)

        # Add next button
        next_btn = js.document.createElement("button")
        next_btn.className = "timeline-btn next-btn"
        next_btn.textContent = "►"
        next_btn.title = "Next Year"
        next_btn.onclick = create_proxy(self.on_next_year)
        controls.appendChild(next_btn)

        # Add the controls to the timeline
        timeline_elem.appendChild(controls)

        # Generate timeline markers
        timeline_track = js.document.createElement("div")
        timeline_track.className = "timeline-track"

        # Sort years for consistent display
        sorted_years = sorted(available_years)
        min_year = sorted_years[0]
        max_year = sorted_years[-1]
        year_range = max_year - min_year

        # Create markers for each available year
        for year in sorted_years:
            # Calculate position based on year
            position = ((year - min_year) / year_range) * 100 if year_range > 0 else 50

            marker = js.document.createElement("div")
            marker.className = f"timeline-marker {'selected' if year == selected_year else ''}"
            marker.style.left = f"{position}%"
            marker.title = str(year)

            # Store the year as a data attribute
            marker.setAttribute("data-year", str(year))

            # Add click handler
            marker.onclick = create_proxy(self.on_marker_click)

            # Add label for every 5th year or if there are few years
            if year % 5 == 0 or len(sorted_years) < 10:
                label = js.document.createElement("span")
                label.className = "timeline-label"
                label.textContent = str(year)
                marker.appendChild(label)

            timeline_track.appendChild(marker)

        # Add the track to the timeline
        timeline_elem.appendChild(timeline_track)

        # Add year selection dropdown
        year_select = js.document.createElement("select")
        year_select.className = "year-select"

        # Add options for each available year
        for year in sorted_years:
            option = js.document.createElement("option")
            option.value = str(year)
            option.textContent = str(year)
            option.selected = year == selected_year
            year_select.appendChild(option)

        # Add change event listener
        year_select.onchange = create_proxy(self.on_year_select_change)

        # Add the year select to the timeline
        timeline_elem.appendChild(year_select)

        # Add loading indicator if needed
        if loading:
            loading_elem = js.document.createElement("div")
            loading_elem.className = "timeline-loading"
            loading_elem.textContent = "Loading..."
            timeline_elem.appendChild(loading_elem)

        # Add the timeline to the container
        self.container.appendChild(timeline_elem)

    def on_marker_click(self, event):
        """
        Handle timeline marker click
        
        Args:
            event: DOM click event
        """
        # Get the year from the data attribute
        year = event.target.getAttribute("data-year")

        if year:
            # Convert to integer
            year = int(year)

            # Get the current city
            state = self.store.get_state()
            city_id = state.get("selected_city_id")

            if city_id:
                # Select the year
                CityActions.select_year(city_id, year)

    def on_year_select_change(self, event):
        """
        Handle year selection dropdown change
        
        Args:
            event: DOM change event
        """
        # Get the selected year
        year = event.target.value

        if year:
            # Convert to integer
            year = int(year)

            # Get the current city
            state = self.store.get_state()
            city_id = state.get("selected_city_id")

            if city_id:
                # Select the year
                CityActions.select_year(city_id, year)

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

        # Ensure animation is stopped
        if self.animation_active:
            SimulationActions.stop_timeline_animation()
