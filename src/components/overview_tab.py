import streamlit as st

class OverviewTab:
    @staticmethod
    def render(data):
        """Render the Overview tab."""
        st.subheader("File Information")
        
        if data.get('file_info', {}).get('type') == 'IFC':
            OverviewTab._render_ifc_info(data)
        else:
            OverviewTab._render_json_info(data)

    @staticmethod
    def _render_ifc_info(data):
        """Render IFC file information."""
        file_info = data.get('file_info', {})
        st.write(f"**File Name:** {file_info.get('name', 'Unknown')}")
        if 'size' in file_info:
            st.write(f"**File Size:** {file_info['size']/1024:.2f} KB")
        st.write(f"**Total Elements:** {data.get('summary', {}).get('total_elements', 0)}")
        
        st.subheader("Element Types Found")
        for element_type in data.get('summary', {}).get('element_types', []):
            st.write(f"- {element_type}")

    @staticmethod
    def _render_json_info(data):
        """Render JSON file information."""
        if isinstance(data, dict):
            st.write("**Structure:** Dictionary")
            st.write(f"**Number of Keys:** {len(data)}")
            st.write("**Top-level Keys:**")
            for key in data.keys():
                st.write(f"- {key}")
        elif isinstance(data, list):
            st.write("**Structure:** List")
            st.write(f"**Number of Items:** {len(data)}")
        
        st.subheader("Data Preview")
        st.json(data)
