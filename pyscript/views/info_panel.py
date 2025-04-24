"""
Information panel component for displaying details about selected objects
"""
import js
import json
import re
from pyodide.ffi import create_proxy
from ..store.app_store import AppStore
from ..actions.city_actions import CityActions
from ..actions.geo_actions import GeoActions
from ..utils.logging import log, error
from ..utils.historical_periods import get_historical_period

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
        self._input_handlers = {}

    def initialize(self):
        """Initialize the component and subscribe to store updates"""
        if self.panel is None or self.content is None:
            js.console.log(f"Warning: Panel elements not found in the DOM")
            return

        self.unsubscribe = self.store.subscribe(create_proxy(self.on_state_change))

        from ..dispatch.dispatcher import Dispatcher
        dispatcher = Dispatcher()
        dispatcher.dispatch("TOGGLE_INFO_PANEL", True)
        
        self.add_panel_controls()

        self.render()

    def add_panel_controls(self):
        """Add control buttons to the panel"""
        header = js.document.querySelector(f"#{self.panel_id} > h2")

        if header:
            controls = js.document.createElement("div")
            controls.className = "panel-controls"
            
            lang_switcher = js.document.createElement("div")
            lang_switcher.className = "language-switcher"
            lang_switcher.style.position = "absolute"
            lang_switcher.style.top = "10px"
            lang_switcher.style.right = "10px"
            
            current_lang = js.document.documentElement.lang or "en"
            
            en_button = js.document.createElement("button")
            en_button.className = "lang-btn"
            if current_lang == "en":
                en_button.classList.add("active")
            en_button.setAttribute("data-lang", "en")
            en_button.textContent = "EN"
            en_button.style.padding = "5px 10px"
            en_button.style.background = "#fff"
            en_button.style.border = "1px solid #ddd"
            en_button.style.borderRadius = "3px 0 0 3px"
            en_button.style.cursor = "pointer"
            self._input_handlers["lang_en"] = create_proxy(lambda e: self._on_language_change(e, "en"))
            en_button.onclick = self._input_handlers["lang_en"]
            
            ru_button = js.document.createElement("button")
            ru_button.className = "lang-btn"
            if current_lang == "ru":
                ru_button.classList.add("active")
            ru_button.setAttribute("data-lang", "ru")
            ru_button.textContent = "RU"
            ru_button.style.padding = "5px 10px"
            ru_button.style.background = "#fff"
            ru_button.style.border = "1px solid #ddd"
            ru_button.style.borderLeft = "none"
            ru_button.style.borderRadius = "0 3px 3px 0"
            ru_button.style.cursor = "pointer"
            self._input_handlers["lang_ru"] = create_proxy(lambda e: self._on_language_change(e, "ru"))
            ru_button.onclick = self._input_handlers["lang_ru"]
            
            lang_switcher.appendChild(en_button)
            lang_switcher.appendChild(ru_button)
            
            js.eval("""
            if (!document.getElementById('lang-btn-style')) {
                var style = document.createElement('style');
                style.id = 'lang-btn-style';
                style.textContent = `
                    .lang-btn.active {
                        background-color: #2196F3 !important;
                        color: white !important;
                        border-color: #2196F3 !important;
                    }
                `;
                document.head.appendChild(style);
            }
            """)
            
            self.panel.appendChild(lang_switcher)
            

            header.appendChild(controls)



    def on_state_change(self, state):
        """
        Handle state changes from the store
        
        Args:
            state: Current application state
        """
        selected_year = state.get("selected_year")
        selected_object = state.get("selected_object")

        self._last_year = selected_year

        if selected_object:
            log(f"InfoPanel: Object selected: {selected_object.get('properties', {}).get('name', 'Unnamed')}")
        
        info_panel_open = state.get("info_panel_open", False)
        log(f"InfoPanel: Panel open state: {info_panel_open}")

        if self.panel:
            self.panel.className = f"info-panel {'' if info_panel_open else 'collapsed'}"

        if info_panel_open:
            self.render()

        if self.panel:
            self.panel.className = f"info-panel {'' if info_panel_open else 'collapsed'}"

        if info_panel_open:
            self.render()

        if self.panel:
            self.panel.className = f"info-panel {'' if info_panel_open else 'collapsed'}"

    def render(self):
        """Render the info panel content based on the current state"""
        if self.content is None:
            return

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

        self.content.innerHTML = ""

        if not selected_object:
            if selected_city:
                self.render_city_info(selected_city, selected_year)
            else:
                message = js.document.createElement("p")
                message.className = "info-message"
                message.textContent = "Please select a city to view information."
                self.content.appendChild(message)
            return

        self.render_object_info(selected_object)

    def render_city_info(self, city, year):
        """
        Render information about the selected city and year
        
        Args:
            city: Selected city object
            year: Selected year
        """
        from ..utils.historical_periods import get_historical_period
        current_lang = js.document.documentElement.lang or "en"
        is_russian = current_lang == "ru"

        city_section = js.document.createElement("div")
        city_section.className = "info-section"

        city_title = js.document.createElement("h3")
        if is_russian:
            city_title.textContent = city["name_ru"]
        else:
            city_title.textContent = city["name"]
        city_section.appendChild(city_title)

        if year:
            year_info = js.document.createElement("p")
            city_section.appendChild(year_info)
            period = get_historical_period(year)
            
            period_section = js.document.createElement("div")
            period_section.className = "historical-period"
            period_title = js.document.createElement("h4")
            period_title.style.marginTop = "15px"
            period_title.style.color = "#2c3e50"
            period_title.textContent = period["name_ru"] if is_russian else period["name"]
            period_section.appendChild(period_title)
            
            period_desc = js.document.createElement("p")
            period_desc.style.fontSize = "0.9em"
            period_desc.style.lineHeight = "1.5"
            period_desc.style.color = "#34495e"
            period_desc.textContent = period["description_ru"] if is_russian else period["description"]
            period_section.appendChild(period_desc)
            
            city_section.appendChild(period_section)

        message = js.document.createElement("p")
        message.className = "info-message"
        message.style.marginTop = "15px"
        message.style.fontStyle = "italic"
        message.style.color = "#7f8c8d"
        city_section.appendChild(message)

        self.content.appendChild(city_section)

    def render_object_info(self, obj):
        """
        Render information about a selected object
        
        Args:
            obj: Selected GeoJSON Feature
        """
        try:
            props = obj.get("properties", {})
            
            state = self.store.get_state()
            current_year = state.get("selected_year")
            
            obj_section = js.document.createElement("div")
            obj_section.className = "info-section"

            name = props.get("name", "Unnamed Object")
            title = js.document.createElement("h3")
            title.textContent = name
            obj_section.appendChild(title)

            if "id" in props:
                id_info = js.document.createElement("p")
                id_info.className = "object-id"
                id_info.textContent = f"ID: {props['id']}"
                obj_section.appendChild(id_info)

            start_date = props.get("start_date")
            end_date = props.get("end_date")
            
            if start_date and current_year:
                try:
                    start_year = int(start_date) if isinstance(start_date, (int, str)) else None
                    end_year = int(end_date) if isinstance(end_date, (int, str)) and end_date != "Present" else None
                    
                    if start_year and start_year <= current_year and (not end_year or current_year <= end_year):
                        age = current_year - start_year
                        context = js.document.createElement("p")
                        context.className = "historical-context"
                        
                        if age == 0:
                            context.textContent = f"This structure was just built in the current year ({current_year})."
                        elif age < 10:
                            context.textContent = f"This is a relatively new structure, built {age} years ago in {start_year}."
                        elif age < 50:
                            context.textContent = f"This structure has been standing for {age} years, since {start_year}."
                        elif age < 100:
                            context.textContent = f"This is a well-established structure built {age} years ago in {start_year}."
                        else:
                            context.textContent = f"This is a historical structure that has stood for {age} years, since {start_year}."
                        
                        context.style.fontStyle = "italic"
                        context.style.color = "#7f8c8d"
                        context.style.marginTop = "10px"
                        obj_section.appendChild(context)
                    elif start_year and start_year > current_year:
                        future = js.document.createElement("p")
                        future.className = "historical-context future"
                        future.textContent = f"Note: This structure will be built {start_year - current_year} years in the future ({start_year})."
                        future.style.color = "#e74c3c"
                        future.style.fontStyle = "italic"
                        obj_section.appendChild(future)
                    elif end_year and current_year > end_year:
                        past = js.document.createElement("p")
                        past.className = "historical-context past"
                        past.textContent = f"Note: This structure no longer exists in {current_year}. It was demolished or replaced in {end_year}."
                        past.style.color = "#e74c3c"
                        past.style.fontStyle = "italic"
                        obj_section.appendChild(past)
                except (ValueError, TypeError):
                    pass

            if "role" in props:
                role_info = js.document.createElement("p")
                role_info.className = "object-role"
                role_info.innerHTML = f"<strong>Type:</strong> {props['role']}"
                obj_section.appendChild(role_info)

            if "description" in props and props["description"]:
                desc_section = js.document.createElement("div")
                desc_section.className = "description-section"

                desc_header = js.document.createElement("h4")
                desc_header.textContent = "Description"
                desc_section.appendChild(desc_header)

                desc_content = js.document.createElement("p")

                try:
                    desc_json = json.loads(props["description"])
                    desc_list = js.document.createElement("ul")
                    desc_list.className = "properties-list"

                    for key, value in desc_json.items():
                        list_item = js.document.createElement("li")
                        list_item.innerHTML = f"<strong>{key}</strong>: {value}"
                        desc_list.appendChild(list_item)

                    desc_section.appendChild(desc_list)
                except:
                    desc_content.textContent = props["description"]
                    desc_section.appendChild(desc_content)

                obj_section.appendChild(desc_section)

            if "start_date" in props or "end_date" in props:
                period_info = js.document.createElement("p")
                period_info.className = "time-period"

                start_date = props.get("start_date", "Unknown")
                end_date = props.get("end_date", "Present")

                period_info.innerHTML = f"<strong>Period:</strong> {start_date} to {end_date}"
                obj_section.appendChild(period_info)

            actions_section = js.document.createElement("div")
            actions_section.className = "actions-section"

            zoom_btn = js.document.createElement("button")
            zoom_btn.className = "action-btn zoom-btn"
            zoom_btn.textContent = "Zoom to Feature"
            zoom_btn.onclick = create_proxy(lambda e: self.zoom_to_feature(obj))
            actions_section.appendChild(zoom_btn)

            export_btn = js.document.createElement("button")
            export_btn.className = "action-btn export-btn"
            export_btn.textContent = "Export GeoJSON"
            export_btn.onclick = create_proxy(lambda e: self.export_feature(obj))
            actions_section.appendChild(export_btn)

            obj_section.appendChild(actions_section)

            self.content.appendChild(obj_section)

            additional_props = {k: v for k, v in props.items()
                                if k not in ['id', 'name', 'role', 'description', 'start_date', 'end_date']}

            if additional_props:
                self.render_additional_properties(additional_props)

        except Exception as e:
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
        add_section = js.document.createElement("div")
        add_section.className = "info-section additional-properties"

        header = js.document.createElement("h4")
        header.textContent = "Additional Properties"
        add_section.appendChild(header)

        props_list = js.document.createElement("ul")
        props_list.className = "properties-list"

        for key, value in props.items():
            item = js.document.createElement("li")
            item.innerHTML = f"<strong>{key}</strong>: {value}"
            props_list.appendChild(item)

        add_section.appendChild(props_list)

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
            feature_json = json.dumps(feature, indent=2)

            blob = js.Blob.new([feature_json], {"type": "application/json"})

            url = js.URL.createObjectURL(blob)

            name = feature.get("properties", {}).get("name", "feature")

            link = js.document.createElement("a")
            link.href = url
            link.download = f"{name}_geojson.json"

            js.document.body.appendChild(link)
            link.click()
            js.document.body.removeChild(link)

            js.URL.revokeObjectURL(url)

        except Exception as e:
            js.console.log(f"Error exporting feature: {str(e)}")

    def cleanup(self):
        """Clean up the component and unsubscribe from the store"""
        if self.unsubscribe:
            self.unsubscribe()

    def _on_language_change(self, event, lang):
        """
        Handle language change
        
        Args:
            event: Click event
            lang: Language code ("en" or "ru")
        """
        if event and hasattr(event, 'stopPropagation'):
            event.stopPropagation()
        
        if lang:
            lang_buttons = js.document.querySelectorAll('.lang-btn')
            for i in range(lang_buttons.length):
                button = lang_buttons.item(i)
                button_lang = button.getAttribute('data-lang')
                if button_lang == lang:
                    if not button.classList.contains('active'):
                        button.classList.add('active')
                else:
                    if button.classList.contains('active'):
                        button.classList.remove('active')
        
            js.document.documentElement.lang = lang
            
            translatable_elements = js.document.querySelectorAll(f'[data-{lang}]')
            for i in range(translatable_elements.length):
                element = translatable_elements.item(i)
                element.textContent = element.getAttribute(f'data-{lang}')

            title_elem = js.document.querySelector(f"#{self.panel_id} > h2")
            if title_elem and title_elem.hasAttribute(f"data-{lang}"):
                title_elem.textContent = title_elem.getAttribute(f"data-{lang}")
            self.render()
