"""
Information panel component for displaying details about selected objects
"""
import js
import json
from pyodide.ffi import create_proxy
from ..store.app_store import AppStore
from ..actions.city_actions import CityActions
from ..actions.geo_actions import GeoActions

class InfoPanel:
    """Information panel component for displaying object details"""
    
    def __init__(self, panel_id="info-panel", content_id="info-content"):
        """
        Initialize the info panel
        
        Args:
            panel_id: ID of the panel container element
            content_id: ID of the content container element
        """
        self.panel_id = panel_id
        self.content_id = content_id
        self.panel = js.document.getElementById(panel_id)
        self.content = js.document.getElementById(content_id)
        self.store = AppStore()
        self.unsubscribe = None
    
    def initialize(self):
        """Initialize the component and subscribe to store updates"""
        if self.panel is None or self.content is None:
            print(f"Warning: Panel elements not found in the DOM")
            return
        
        # Subscribe to store changes
        self.unsubscribe = self.store.subscribe(create_proxy(self.on_state_change))
        
        # Add close button to the panel
        self.add_panel_controls()
        
        # Initial render
        self.render()
    
    def add_panel_controls(self):
        """Add control buttons to the panel"""
        # Add a header with controls if it doesn't exist
        header = js.document.querySelector(f"#{self.panel_id} > h2")
        
        if header:
            # Create a controls container
            controls = js.document.createElement("div")
            controls.className = "panel-controls"
            
            # Add close button
            close_btn = js.document.createElement("button")
            close_btn.className = "close-btn"
            close_btn.textContent = "✕"
            close_btn.title = "Close panel"
            close_btn.onclick = create_proxy(self.on_close_panel)
            controls.appendChild(close_btn)
            
            # Add the controls after the header
            header.appendChild(controls)
    
    def on_state_change(self, state):
        """
        Handle state changes from the store
        
        Args:
            state: Current application state
        """
        # Get panel visibility state
        info_panel_open = state.get("info_panel_open", False)
        
        # Update panel visibility
        if self.panel:
            self.panel.className = f"info-panel {'' if info_panel_open else 'collapsed'}"
        
        # Render content if the panel is open
        if info_panel_open:
            self.render()
    
    def render(self):
        """Render the info panel content based on the current state"""
        if self.content is None:
            return
        
        # Get the current state
        state = self.store.get_state()
        selected_object = state.get("selected_object")
        selected_city = None
        selected_year = None
        
        city_id = state.get("selected_city_id")
        if city_id:
            for city in state.get("cities", []):
                if city["id"] == city_id:
                    selected_city = city
                    break
        
        selected_year = state.get("selected_year")
        
        # Clear content
        self.content.innerHTML = ""
        
        # If no object is selected, show city and year info
        if not selected_object:
            if selected_city:
                self.render_city_info(selected_city, selected_year)
            else:
                # No city selected
                message = js.document.createElement("p")
                message.className = "info-message"
                message.textContent = "Please select a city to view information."
                self.content.appendChild(message)
            return
        
        # Render selected object information
        self.render_object_info(selected_object)
    
    def render_city_info(self, city, year):
        """
        Render information about the selected city and year
        
        Args:
            city: Selected city object
            year: Selected year
        """
        # Create city info section
        city_section = js.document.createElement("div")
        city_section.className = "info-section"
        
        # City title
        city_title = js.document.createElement("h3")
        city_title.textContent = city["name"]
        city_section.appendChild(city_title)
        
        # Year info
        if year:
            year_info = js.document.createElement("p")
            year_info.textContent = f"Showing data for year: {year}"
            city_section.appendChild(year_info)
        
        # Add message to select an object
        message = js.document.createElement("p")
        message.className = "info-message"
        message.textContent = "Click on a map feature to view its details."
        city_section.appendChild(message)
        
        # Add to content
        self.content.appendChild(city_section)
    
    def render_object_info(self, obj):
        """
        Render information about a selected object
        
        Args:
            obj: Selected GeoJSON Feature
        """
        try:
            # Get properties from the object
            props = obj.get("properties", {})
            
            # Create object info section
            obj_section = js.document.createElement("div")
            obj_section.className = "info-section"
            
            # Object title
            name = props.get("name", "Unnamed Object")
            title = js.document.createElement("h3")
            title.textContent = name
            obj_section.appendChild(title)
            
            # Object ID
            if "id" in props:
                id_info = js.document.createElement("p")
                id_info.className = "object-id"
                id_info.textContent = f"ID: {props['id']}"
                obj_section.appendChild(id_info)
            
            # Object role/type
            if "role" in props:
                role_info = js.document.createElement("p")
                role_info.className = "object-role"
                role_info.innerHTML = f"<strong>Type:</strong> {props['role']}"
                obj_section.appendChild(role_info)
            
            # Description
            if "description" in props and props["description"]:
                # Create description section
                desc_section = js.document.createElement("div")
                desc_section.className = "description-section"
                
                # Description header
                desc_header = js.document.createElement("h4")
                desc_header.textContent = "Description"
                desc_section.appendChild(desc_header)
                
                # Description content
                desc_content = js.document.createElement("p")
                
                # Check if description is JSON
                try:
                    desc_json = json.loads(props["description"])
                    # Format as properties list
                    desc_list = js.document.createElement("ul")
                    desc_list.className = "properties-list"
                    
                    for key, value in desc_json.items():
                        list_item = js.document.createElement("li")
                        list_item.innerHTML = f"<strong>{key}</strong>: {value}"
                        desc_list.appendChild(list_item)
                    
                    desc_section.appendChild(desc_list)
                except:
                    # Not JSON, use as plain text
                    desc_content.textContent = props["description"]
                    desc_section.appendChild(desc_content)
                
                obj_section.appendChild(desc_section)
            
            # Time period (if available)
            if "start_date" in props or "end_date" in props:
                period_info = js.document.createElement("p")
                period_info.className = "time-period"
                
                start_date = props.get("start_date", "Unknown")
                end_date = props.get("end_date", "Present")
                
                period_info.innerHTML = f"<strong>Period:</strong> {start_date} to {end_date}"
                obj_section.appendChild(period_info)
            
            # Add actions section
            actions_section = js.document.createElement("div")
            actions_section.className = "actions-section"
            
            # Zoom to feature button
            zoom_btn = js.document.createElement("button")
            zoom_btn.className = "action-btn zoom-btn"
            zoom_btn.textContent = "Zoom to Feature"
            zoom_btn.onclick = create_proxy(lambda e: self.zoom_to_feature(obj))
            actions_section.appendChild(zoom_btn)
            
            # Export feature button
            export_btn = js.document.createElement("button")
            export_btn.className = "action-btn export-btn"
            export_btn.textContent = "Export GeoJSON"
            export_btn.onclick = create_proxy(lambda e: self.export_feature(obj))
            actions_section.appendChild(export_btn)
            
            obj_section.appendChild(actions_section)
            
            # Add to content
            self.content.appendChild(obj_section)
            
            # Add additional data section if there's more in properties
            additional_props = {k: v for k, v in props.items() 
                              if k not in ['id', 'name', 'role', 'description', 'start_date', 'end_date']}
            
            if additional_props:
                self.render_additional_properties(additional_props)
            
        except Exception as e:
            # Handle errors
            error_msg = js.document.createElement("p")
            error_msg.className = "error-message"
            error_msg.textContent = f"Error displaying object information: {str(e)}"
            self.content.appendChild(error_msg)
    
    def render_additional_properties(self, props):
        """
        Render additional properties of an object
        
        Args:
            props: Dictionary of additional properties
        """
        # Create additional info section
        add_section = js.document.createElement("div")
        add_section.className = "info-section additional-properties"
        
        # Section header
        header = js.document.createElement("h4")
        header.textContent = "Additional Properties"
        add_section.appendChild(header)
        
        # Create properties list
        props_list = js.document.createElement("ul")
        props_list.className = "properties-list"
        
        # Add each property
        for key, value in props.items():
            item = js.document.createElement("li")
            item.innerHTML = f"<strong>{key}</strong>: {value}"
            props_list.appendChild(item)
        
        add_section.appendChild(props_list)
        
        # Add to content
        self.content.appendChild(add_section)
    
    def zoom_to_feature(self, feature):
        """
        Zoom the map to the selected feature
        
        Args:
            feature: GeoJSON Feature to zoom to
        """
        GeoActions.select_geo_object(feature, center_map=True)
    
    def export_feature(self, feature):
        """
        Export the selected feature as GeoJSON
        
        Args:
            feature: GeoJSON Feature to export
        """
        try:
            # Convert to JSON string
            feature_json = json.dumps(feature, indent=2)
            
            # Create a blob
            blob = js.Blob.new([feature_json], {"type": "application/json"})
            
            # Create an object URL
            url = js.URL.createObjectURL(blob)
            
            # Get feature name for the filename
            name = feature.get("properties", {}).get("name", "feature")
            name = name.replace(/[^a-z0-9]/gi, '_').lower()
            
            # Create a temporary link element
            link = js.document.createElement("a")
            link.href = url
            link.download = f"{name}_geojson.json"
            
            # Append to body, click, and remove
            js.document.body.appendChild(link)
            link.click()
            js.document.body.removeChild(link)
            
            # Clean up the URL
            js.URL.revokeObjectURL(url)
            
        except Exception as e:
            print(f"Error exporting feature: {str(e)}")
    
    def on_close_panel(self, event):
        """Handle close panel button click"""
        GeoActions.toggle_info_panel(False)
    
    def cleanup(self):
        """Clean up the component and unsubscribe from the store"""
        if self.unsubscribe:
            self.unsubscribe()

