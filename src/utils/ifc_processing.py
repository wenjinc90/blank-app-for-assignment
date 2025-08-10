"""
IFC Processing utilities for extracting and structuring building information from IFC files.
"""

import json
import os
from typing import Dict, List, Any, Optional
import tempfile

try:
    import ifcopenshell
    IFCOPENSHELL_AVAILABLE = True
except ImportError:
    IFCOPENSHELL_AVAILABLE = False


class IFCProcessor:
    """Class for processing IFC files and extracting relevant building information."""
    
    def __init__(self):
        if not IFCOPENSHELL_AVAILABLE:
            raise ImportError(
                "ifcopenshell is required for IFC processing. "
                "Install it with: pip install ifcopenshell"
            )
        # Cache for storing text chunks
        self._text_chunks_cache = {}
    
    def load_ifc_file(self, file_path: str) -> Any:
        """Load an IFC file using ifcopenshell."""
        try:
            ifc_file = ifcopenshell.open(file_path)
            return ifc_file
        except Exception as e:
            raise ValueError(f"Error loading IFC file: {e}")
    
    def extract_building_elements(self, ifc_file: Any) -> List[Dict]:
        """Extract building elements from IFC file with their properties."""
        elements = []
        
        # Common IFC element types to extract
        element_types = [
            'IfcWall', 'IfcSlab', 'IfcBeam', 'IfcColumn', 'IfcDoor', 'IfcWindow',
            'IfcStair', 'IfcRailing', 'IfcRoof', 'IfcCurtainWall', 'IfcBuildingElementProxy'
        ]
        
        for element_type in element_types:
            try:
                ifc_elements = ifc_file.by_type(element_type)
                for element in ifc_elements:
                    # Changed to include_properties=True
                    element_data = self.extract_element_data(
                        element, 
                        include_properties=True,  # Set to True to extract properties
                        include_geometry=False
                    )
                    if element_data:
                        elements.append(element_data)
            except Exception as e:
                print(f"Warning: Error processing {element_type}: {e}")
                continue
        
        return elements
    
    def extract_element_data(self, element: Any, include_properties: bool = False, include_geometry: bool = False) -> Dict:
        """Extract relevant data from a single IFC element.
        
        Args:
            element: The IFC element to process
            include_properties: Whether to include detailed property information
            include_geometry: Whether to include geometry information
        """
        try:
            # Extract basic element data (fast)
            element_data = {
                'id': getattr(element, 'GlobalId', str(element.id())),
                'type': element.is_a(),
                'name': getattr(element, 'Name', '') or '',
                'description': getattr(element, 'Description', '') or '',
                'properties': {}
            }
            
            # Only extract properties if requested (slow operation)
            if include_properties and hasattr(element, 'IsDefinedBy'):
                for definition in element.IsDefinedBy:
                    if definition.is_a('IfcRelDefinesByProperties'):
                        property_set = definition.RelatingPropertyDefinition
                        if property_set.is_a('IfcPropertySet'):
                            ps_name = property_set.Name
                            element_data['properties'][ps_name] = {}
                            
                            for prop in property_set.HasProperties:
                                if prop.is_a('IfcPropertySingleValue'):
                                    prop_name = prop.Name
                                    prop_value = prop.NominalValue.wrappedValue if prop.NominalValue else None
                                    element_data['properties'][ps_name][prop_name] = {
                                        'value': prop_value,
                                        'unit': getattr(prop.NominalValue, 'Unit', None) if prop.NominalValue else None
                                    }
            
            # Only extract geometry if requested (slow operation)
            if include_geometry:
                element_data['geometry'] = self.extract_geometry_info(element)
            
            return element_data
            
        except Exception as e:
            print(f"Warning: Error extracting data from element {element}: {e}")
            return None
    
    def extract_geometry_info(self, element: Any) -> Dict:
        """Extract basic geometry information from an element."""
        geometry = {}
        
        try:
            # Try to get basic dimensions
            if hasattr(element, 'Representation') and element.Representation:
                # This is a simplified approach - real geometry extraction is complex
                geometry['has_geometry'] = True
            else:
                geometry['has_geometry'] = False
                
            # Extract location if available
            if hasattr(element, 'ObjectPlacement') and element.ObjectPlacement:
                geometry['has_placement'] = True
            else:
                geometry['has_placement'] = False
                
        except Exception as e:
            print(f"Warning: Error extracting geometry from element: {e}")
            
        return geometry
    
    def clear_cache(self):
        """Clear the text chunks cache."""
        self._text_chunks_cache = {}

    def process_uploaded_ifc(self, uploaded_file) -> Dict:
        """Process an uploaded IFC file from Streamlit file uploader."""
        try:
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ifc') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Process the IFC file
            ifc_file = self.load_ifc_file(tmp_path)
            elements = self.extract_building_elements(ifc_file)
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            # Structure data similar to JSON format expected by the app
            processed_data = {
                'file_info': {
                    'name': uploaded_file.name,
                    'size': len(uploaded_file.getvalue()),
                    'type': 'IFC'
                },
                'elements': elements,
                'summary': {
                    'total_elements': len(elements),
                    'element_types': list(set(el['type'] for el in elements))
                }
            }
            
            return processed_data
            
        except Exception as e:
            raise ValueError(f"Error processing uploaded IFC file: {e}")
    
    def process_sample_ifc(self, file_path: str) -> Dict:
        """Process a sample IFC file from the sample_models folder."""
        try:
            ifc_file = self.load_ifc_file(file_path)
            elements = self.extract_building_elements(ifc_file)
            
            # Structure data similar to JSON format expected by the app
            processed_data = {
                'file_info': {
                    'name': os.path.basename(file_path),
                    'path': file_path,
                    'type': 'IFC'
                },
                'elements': elements,
                'summary': {
                    'total_elements': len(elements),
                    'element_types': list(set(el['type'] for el in elements))
                }
            }
            
            return processed_data
            
        except Exception as e:
            raise ValueError(f"Error processing sample IFC file: {e}")
    
    def convert_to_text_chunks(self, processed_data: Dict, batch_size: int = 100, use_cache: bool = True) -> List[str]:
        """Convert processed IFC data to text chunks suitable for embedding."""
        # Generate cache key
        file_info = processed_data.get('file_info', {})
        cache_key = f"{file_info.get('name', '')}_{file_info.get('size', 0)}"
        
        if use_cache and cache_key in self._text_chunks_cache:
            return self._text_chunks_cache[cache_key]
            
        texts = []
        elements = processed_data.get('elements', [])
        
        for i in range(0, len(elements), batch_size):
            batch = elements[i:i + batch_size]
            
            for element in batch:
                text_parts = []
                
                # Basic element information
                text_parts.append(f"Element Type: {element.get('type', 'Unknown')}")
                text_parts.append(f"ID: {element.get('id', 'Unknown')}")
                text_parts.append(f"Global ID: {element.get('globalId', 'Unknown')}")
                
                if element.get('name'):
                    text_parts.append(f"Name: {element.get('name')}")
                
                if element.get('description'):
                    text_parts.append(f"Description: {element.get('description')}")
                
                # Include ALL properties
                for ps_name, properties in element.get('properties', {}).items():
                    if isinstance(properties, dict):
                        # Handle nested property structure
                        for prop_name, prop_data in properties.items():
                            if isinstance(prop_data, dict):
                                value = prop_data.get('value')
                                unit = prop_data.get('unit', '')
                                prop_type = prop_data.get('type', '')
                                
                                if value is not None:
                                    prop_text = f"{ps_name} - {prop_name}: {value}"
                                    if unit:
                                        prop_text += f" {unit}"
                                    if prop_type:
                                        prop_text += f" (Type: {prop_type})"
                                    text_parts.append(prop_text)
                            else:
                                # Direct property value
                                text_parts.append(f"{ps_name} - {prop_name}: {prop_data}")
                    else:
                        # Direct property set value
                        text_parts.append(f"{ps_name}: {properties}")
                
                # Join all information with separators
                element_text = " | ".join(filter(None, text_parts))
                texts.append(element_text)
        
        if use_cache:
            self._text_chunks_cache[cache_key] = texts
        
        return texts
    
    def save_to_json(self, processed_data: Dict, output_path: str = None) -> str:
        """Save processed IFC data to JSON file."""
        try:
            if output_path is None:
                # Generate default filename based on original IFC file
                original_name = processed_data.get('file_info', {}).get('name', 'processed_ifc')
                if original_name.endswith('.ifc'):
                    json_name = original_name.replace('.ifc', '_processed.json')
                else:
                    json_name = f"{original_name}_processed.json"
                output_path = json_name
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
            
            return output_path
            
        except Exception as e:
            raise ValueError(f"Error saving JSON file: {e}")
    
    def get_json_string(self, processed_data: Dict, compact: bool = True) -> str:
        """Convert processed IFC data to JSON string for download.
        
        Args:
            processed_data: The data to convert to JSON
            compact: If True, uses a more compact JSON format to reduce size
        """
        try:
            if compact:
                # Use compact format without indentation for better performance
                return json.dumps(
                    processed_data,
                    ensure_ascii=False,
                    separators=(',', ':')  # Remove whitespace
                )
            return json.dumps(processed_data, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ValueError(f"Error converting to JSON string: {e}")
    
    @staticmethod
    def process_ifc(ifc_file) -> Dict[str, Any]:
        """Process an IFC file and extract all available parameters."""
        ifc = ifcopenshell.open(ifc_file)
        elements = []

        for entity in ifc:
            if hasattr(entity, 'is_a') and not entity.is_a('IfcRelationship'):
                element_data = {
                    'id': entity.id(),
                    'type': entity.is_a(),
                    'name': getattr(entity, 'Name', None),
                    'globalId': getattr(entity, 'GlobalId', None),
                    'properties': {}
                }

                # 1. Extract all direct attributes
                for attribute in entity.get_info().keys():
                    try:
                        value = getattr(entity, attribute)
                        if value is not None:
                            element_data['properties'][attribute] = {
                                'value': str(value),
                                'type': type(value).__name__
                            }
                    except:
                        continue

                # 2. Extract property sets (Psets)
                if entity.is_a('IfcObject'):
                    for definition in entity.IsDefinedBy:
                        if definition.is_a('IfcRelDefinesByProperties'):
                            pset = definition.RelatingPropertyDefinition
                            if pset.is_a('IfcPropertySet'):
                                for prop in pset.HasProperties:
                                    if prop.is_a('IfcPropertySingleValue'):
                                        element_data['properties'][f"{pset.Name}.{prop.Name}"] = {
                                            'value': str(prop.NominalValue.wrappedValue) if prop.NominalValue else None,
                                            'type': prop.NominalValue.is_a() if prop.NominalValue else None,
                                            'unit': str(prop.Unit) if hasattr(prop, 'Unit') else None
                                        }

                # 3. Extract quantities
                for definition in entity.IsDefinedBy:
                    if definition.is_a('IfcRelDefinesByProperties'):
                        qset = definition.RelatingPropertyDefinition
                        if qset.is_a('IfcElementQuantity'):
                            for quantity in qset.Quantities:
                                if hasattr(quantity, 'Name'):
                                    element_data['properties'][f"{qset.Name}.{quantity.Name}"] = {
                                        'value': getattr(quantity, quantity.is_a()[3:], None),
                                        'type': quantity.is_a(),
                                        'unit': str(quantity.Unit) if hasattr(quantity, 'Unit') else None
                                    }

                # 4. Extract material information
                if hasattr(entity, 'HasAssociations'):
                    for association in entity.HasAssociations:
                        if association.is_a('IfcRelAssociatesMaterial'):
                            material = association.RelatingMaterial
                            if material.is_a('IfcMaterial'):
                                element_data['properties']['Material'] = {
                                    'value': material.Name,
                                    'type': 'IfcMaterial'
                                }

                elements.append(element_data)

        return {
            'elements': elements,
            'file_info': {
                'schema': ifc.schema,
                'header': ifc.header
            }
        }


def check_ifcopenshell_installation() -> bool:
    """Check if ifcopenshell is available."""
    return IFCOPENSHELL_AVAILABLE


def install_ifcopenshell_message() -> str:
    """Return installation message for ifcopenshell."""
    return """
    To process IFC files, you need to install ifcopenshell:
    
    ```bash
    pip install ifcopenshell
    ```
    
    Note: ifcopenshell requires Python 3.6+ and may have platform-specific requirements.
    """
