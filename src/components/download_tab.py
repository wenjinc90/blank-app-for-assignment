import streamlit as st
import os
from src.utils.ifc_processing import IFCProcessor

class DownloadTab:
    @staticmethod
    def render(data):
        """Render the Download tab."""
        if data.get('file_info', {}).get('type') == 'IFC':
            DownloadTab._render_ifc_download(data)
        else:
            st.json(data)

    @staticmethod
    def _render_ifc_download(data):
        """Render IFC file download options."""
        try:
            processor = IFCProcessor()
            json_string = processor.get_json_string(data)
            
            # Generate filename for download
            original_name = data.get('file_info', {}).get('name', 'processed_ifc')
            download_filename = DownloadTab._generate_download_filename(original_name)
            
            st.write("### Download Processed IFC Data")
            st.write("Download the processed IFC data in JSON format for use in other applications.")
            st.download_button(
                label="📥 Download as JSON",
                data=json_string,
                file_name=download_filename,
                mime="application/json",
                help="Download the processed IFC data in JSON format"
            )
            
            # Show preview of the JSON
            st.write("### JSON Preview")
            st.json(data)
        except Exception as e:
            st.error(f"Error preparing download: {e}")

    @staticmethod
    def _generate_download_filename(original_name):
        """Generate a download filename based on the original name."""
        if original_name.endswith('.ifc'):
            return original_name.replace('.ifc', '_processed.json')
        return f"{original_name}_processed.json"
