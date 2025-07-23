import os
import json
from typing import Dict, Optional, Union
import streamlit as st
from src.utils.ifc_processing import IFCProcessor, check_ifcopenshell_installation, install_ifcopenshell_message

class FileLoader:
    @staticmethod
    def list_sample_models(sample_models_dir: str) -> list:
        """List all sample models in the given directory."""
        return [
            f for f in os.listdir(sample_models_dir)
            if (f.endswith(".json") or f.endswith(".ifc")) and os.path.isfile(os.path.join(sample_models_dir, f))
        ]

    @staticmethod
    def load_sample_file(sample_file_path: str) -> Optional[Dict]:
        """Load a sample file (JSON or IFC)."""
        if not os.path.exists(sample_file_path):
            st.error(f"Sample model not found at {sample_file_path}")
            return None

        if sample_file_path.endswith('.json'):
            return FileLoader._load_json_file(sample_file_path)
        elif sample_file_path.endswith('.ifc'):
            return FileLoader._load_ifc_file(sample_file_path)
        return None

    @staticmethod
    def load_uploaded_file(uploaded_file) -> Optional[Dict]:
        """Load an uploaded file (JSON or IFC)."""
        if uploaded_file.name.endswith('.json'):
            return FileLoader._load_uploaded_json(uploaded_file)
        elif uploaded_file.name.endswith('.ifc'):
            return FileLoader._load_uploaded_ifc(uploaded_file)
        return None

    @staticmethod
    def _load_json_file(file_path: str) -> Optional[Dict]:
        """Load a JSON file from disk."""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            st.success(f"Sample JSON model loaded!")
            return data
        except Exception as e:
            st.error(f"Error reading JSON file: {e}")
            return None

    @staticmethod
    def _load_uploaded_json(uploaded_file) -> Optional[Dict]:
        """Load an uploaded JSON file."""
        try:
            data = json.load(uploaded_file)
            st.success("JSON file uploaded successfully!")
            return data
        except Exception as e:
            st.error(f"Error reading JSON file: {e}")
            return None

    @staticmethod
    def _load_ifc_file(file_path: str) -> Optional[Dict]:
        """Load an IFC file from disk."""
        if not check_ifcopenshell_installation():
            st.error("ifcopenshell is required to process IFC files")
            st.info(install_ifcopenshell_message())
            return None

        try:
            processor = IFCProcessor()
            data = processor.process_sample_ifc(file_path)
            st.success(f"Sample IFC model processed!")
            st.info(f"Processed {data['summary']['total_elements']} elements from IFC file")
            return data
        except Exception as e:
            st.error(f"Error processing IFC file: {e}")
            return None

    @staticmethod
    def _load_uploaded_ifc(uploaded_file) -> Optional[Dict]:
        """Load an uploaded IFC file."""
        if not check_ifcopenshell_installation():
            st.error("ifcopenshell is required to process IFC files")
            st.info(install_ifcopenshell_message())
            return None

        try:
            processor = IFCProcessor()
            data = processor.process_uploaded_ifc(uploaded_file)
            st.success("IFC file uploaded and processed successfully!")
            st.info(f"Processed {data['summary']['total_elements']} elements from IFC file")
            return data
        except Exception as e:
            st.error(f"Error processing IFC file: {e}")
            return None
