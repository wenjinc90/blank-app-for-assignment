import streamlit as st

class ElementsTab:
    @staticmethod
    def render(data):
        """Render the Elements tab."""
        if data.get('file_info', {}).get('type') == 'IFC':
            ElementsTab._render_ifc_elements(data)
        else:
            ElementsTab._render_json_elements(data)

    @staticmethod
    def _render_ifc_elements(data):
        """Render IFC elements view."""
        st.subheader("Building Elements")
        
        elements = data.get('elements', [])
        if not elements:
            st.warning("No elements found in the IFC file.")
            return
        
        # Add element type filter
        element_types = data.get('summary', {}).get('element_types', [])
        selected_type = st.selectbox("Filter by Element Type", ["All"] + element_types)
        
        # Add search box
        search_query = st.text_input("Search elements", "")
        
        # Display elements with filtering and search
        filtered_count = ElementsTab._display_filtered_elements(
            elements, selected_type, search_query)
        
        # Show statistics
        st.sidebar.write(f"Showing {filtered_count} of {len(elements)} elements")

    @staticmethod
    def _display_filtered_elements(elements, selected_type, search_query):
        """Display filtered elements and return count."""
        filtered_count = 0
        for element in elements:
            try:
                if ElementsTab._should_display_element(element, selected_type, search_query):
                    filtered_count += 1
                    ElementsTab._display_element(element)
            except Exception as e:
                st.error(f"Error displaying element: {str(e)}")
                continue
        return filtered_count

    @staticmethod
    def _should_display_element(element, selected_type, search_query):
        """Check if element should be displayed based on filters."""
        return (selected_type == "All" or element.get('type') == selected_type) and \
               (not search_query or search_query.lower() in str(element).lower())

    @staticmethod
    def _display_element(element):
        """Display a single element."""
        with st.expander(f"{element.get('type', 'Unknown')} - {element.get('name', 'Unnamed')}"):
            st.write("**ID:** ", element.get('id', 'No ID'))
            if element.get('description'):
                st.write("**Description:** ", element['description'])
            
            ElementsTab._display_properties(element)
            ElementsTab._display_geometry(element)

    @staticmethod
    def _display_properties(element):
        """Display element properties."""
        if element.get('properties'):
            for ps_name, properties in element['properties'].items():
                st.write(f"**{ps_name}**")
                for prop_name, prop_data in properties.items():
                    value = prop_data.get('value', '')
                    unit = prop_data.get('unit', '')
                    if value is not None:  # Allow 0 values
                        st.write(f"- {prop_name}: {value} {unit if unit else ''}")
        else:
            st.info("No properties found for this element.")

    @staticmethod
    def _display_geometry(element):
        """Display element geometry information."""
        if element.get('geometry'):
            st.write("**Geometry Information:**")
            for geo_key, geo_value in element['geometry'].items():
                st.write(f"- {geo_key}: {geo_value}")

    @staticmethod
    def _render_json_elements(data):
        """Render JSON elements view."""
        st.subheader("JSON Data Explorer")
        
        if isinstance(data, dict):
            ElementsTab._display_dict_data(data)
        elif isinstance(data, list):
            ElementsTab._display_list_data(data)
        else:
            st.json(data)

    @staticmethod
    def _display_dict_data(data):
        """Display dictionary data."""
        search_query = st.text_input("Search in JSON", "")
        for key, value in data.items():
            if not search_query or search_query.lower() in str(key).lower() or \
               search_query.lower() in str(value).lower():
                with st.expander(f"Key: {key}"):
                    st.json(value)

    @staticmethod
    def _display_list_data(data):
        """Display list data."""
        search_query = st.text_input("Search in list items", "")
        for i, item in enumerate(data):
            if not search_query or search_query.lower() in str(item).lower():
                with st.expander(f"Item {i+1}"):
                    st.json(item)
