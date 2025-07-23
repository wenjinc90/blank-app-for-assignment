import streamlit as st
import json
import os
from utils.ifc_processing import IFCProcessor, check_ifcopenshell_installation, install_ifcopenshell_message
from utils.embedding import EmbeddingProcessor

st.title("🎈 My new app")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)

# List all sample models in the folder
sample_models_dir = "sample_models"
sample_files = [
    f for f in os.listdir(sample_models_dir)
    if (f.endswith(".json") or f.endswith(".ifc")) and os.path.isfile(os.path.join(sample_models_dir, f))
]

selected_sample = st.selectbox(
    "Or select a sample model:",
    ["None"] + sample_files
)

# JSON/IFC file uploader
uploaded_file = st.file_uploader("Upload a JSON or IFC file", type=["json", "ifc"])

data = None
if selected_sample != "None":
    sample_file_path = os.path.join(sample_models_dir, selected_sample)
    if os.path.exists(sample_file_path):
        if selected_sample.endswith('.json'):
            # Load JSON file
            with open(sample_file_path, "r") as f:
                data = json.load(f)
            st.success(f"Sample JSON model '{selected_sample}' loaded!")
        elif selected_sample.endswith('.ifc'):
            # Process IFC file
            if check_ifcopenshell_installation():
                try:
                    processor = IFCProcessor()
                    data = processor.process_sample_ifc(sample_file_path)
                    st.success(f"Sample IFC model '{selected_sample}' processed!")
                    st.info(f"Processed {data['summary']['total_elements']} elements from IFC file")
                except Exception as e:
                    st.error(f"Error processing IFC file: {e}")
            else:
                st.error("ifcopenshell is required to process IFC files")
                st.info(install_ifcopenshell_message())
    else:
        st.error(f"Sample model not found at {sample_file_path}")
elif uploaded_file is not None:
    if uploaded_file.name.endswith('.json'):
        # Load JSON file
        try:
            data = json.load(uploaded_file)
            st.success("JSON file uploaded successfully!")
        except Exception as e:
            st.error(f"Error reading JSON file: {e}")
    elif uploaded_file.name.endswith('.ifc'):
        # Process IFC file
        if check_ifcopenshell_installation():
            try:
                processor = IFCProcessor()
                data = processor.process_uploaded_ifc(uploaded_file)
                st.success("IFC file uploaded and processed successfully!")
                st.info(f"Processed {data['summary']['total_elements']} elements from IFC file")
            except Exception as e:
                st.error(f"Error processing IFC file: {e}")
        else:
            st.error("ifcopenshell is required to process IFC files")
            st.info(install_ifcopenshell_message())

if data:
    # Create tabs for different views of the data
    tab_overview, tab_elements, tab_download, tab_embeddings = st.tabs([
        "Overview", "Building Elements", "Download", "Embeddings"
    ])
    
    with tab_overview:
        st.subheader("File Information")
        
        if data.get('file_info', {}).get('type') == 'IFC':
            # For IFC files
            file_info = data.get('file_info', {})
            st.write(f"**File Name:** {file_info.get('name', 'Unknown')}")
            if 'size' in file_info:
                st.write(f"**File Size:** {file_info['size']/1024:.2f} KB")
            st.write(f"**Total Elements:** {data.get('summary', {}).get('total_elements', 0)}")
            
            st.subheader("Element Types Found")
            for element_type in data.get('summary', {}).get('element_types', []):
                st.write(f"- {element_type}")
        else:
            # For JSON files
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

    with tab_elements:
        if data.get('file_info', {}).get('type') == 'IFC':
            st.subheader("Building Elements")
            
            elements = data.get('elements', [])
            if not elements:
                st.warning("No elements found in the IFC file.")
                st.stop()
            
            # Add element type filter
            element_types = data.get('summary', {}).get('element_types', [])
            selected_type = st.selectbox("Filter by Element Type", ["All"] + element_types)
            
            # Add search box
            search_query = st.text_input("Search elements", "")
            
            # Count elements for statistics
            filtered_count = 0
            
            # Display elements with filtering and search
            for element in elements:
                try:
                    if (selected_type == "All" or element.get('type') == selected_type) and \
                       (not search_query or search_query.lower() in str(element).lower()):
                        filtered_count += 1
                        with st.expander(f"{element.get('type', 'Unknown')} - {element.get('name', 'Unnamed')}"):
                            st.write("**ID:** ", element.get('id', 'No ID'))
                            if element.get('description'):
                                st.write("**Description:** ", element['description'])
                            
                            # Display properties in a more organized way
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
                            
                            # Display geometry information
                            if element.get('geometry'):
                                st.write("**Geometry Information:**")
                                for geo_key, geo_value in element['geometry'].items():
                                    st.write(f"- {geo_key}: {geo_value}")
                except Exception as e:
                    st.error(f"Error displaying element: {str(e)}")
                    continue
            
            # Show statistics
            st.sidebar.write(f"Showing {filtered_count} of {len(elements)} elements")
            
        else:
            # For JSON data, show structured view
            st.subheader("JSON Data Explorer")
            
            if isinstance(data, dict):
                # For dictionary data
                search_query = st.text_input("Search in JSON", "")
                for key, value in data.items():
                    if not search_query or search_query.lower() in str(key).lower() or search_query.lower() in str(value).lower():
                        with st.expander(f"Key: {key}"):
                            st.json(value)
            elif isinstance(data, list):
                # For list data
                search_query = st.text_input("Search in list items", "")
                for i, item in enumerate(data):
                    if not search_query or search_query.lower() in str(item).lower():
                        with st.expander(f"Item {i+1}"):
                            st.json(item)
            else:
                st.json(data)
    
    with tab_download:
        if data.get('file_info', {}).get('type') == 'IFC':
            try:
                processor = IFCProcessor()
                json_string = processor.get_json_string(data)
                
                # Generate filename for download
                original_name = data.get('file_info', {}).get('name', 'processed_ifc')
                if original_name.endswith('.ifc'):
                    download_filename = original_name.replace('.ifc', '_processed.json')
                else:
                    download_filename = f"{original_name}_processed.json"
                
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
        else:
            st.json(data)

    # Create embeddings tab
    tab_embeddings = st.tabs(["Embeddings"])[0]
    with tab_embeddings:
        st.subheader("Text Embeddings")
        st.write("Convert building elements to text descriptions for embedding and semantic search.")
        
        # Initialize embedding processor
        embedding_processor = EmbeddingProcessor()
        
        # Add model selection
        embedding_models = embedding_processor.get_available_models()
        selected_model = st.selectbox(
            "Select Embedding Model:",
            list(embedding_models.keys()),
            index=0,
            help="Choose the OpenAI embedding model to use"
        )
        st.info(f"Model Info: {embedding_models[selected_model]}")
        
        # Add OpenAI API Key input here
        openai_api_key = st.text_input("Enter your OpenAI API key:", type="password")
        
        if openai_api_key:
            embedding_processor.set_api_key(openai_api_key)
            embedding_processor.set_model(selected_model)
        
        if data.get('file_info', {}).get('type') == 'IFC':
            try:
                processor = IFCProcessor()
                texts = processor.convert_to_text_chunks(data)
                
                # Show a sample of texts with expanders
                st.write("### Text Descriptions")
                st.write("Below are the text descriptions that will be used for embeddings. Each description includes all available properties of the building element.")
                
                for i, text in enumerate(texts):
                    with st.expander(f"Element {i+1}"):
                        st.write(text)
                
            except Exception as e:
                st.error(f"Error converting elements to text: {e}")
        else:
            # For JSON files, use the existing text extraction
            elements = data.get("elements", [])
            texts = []
            for el in elements:
                if isinstance(el, dict):
                    text_parts = []
                    # Include all available fields
                    for key, value in el.items():
                        if key != 'properties':  # Handle properties separately
                            text_parts.append(f"{key}: {value}")
                    
                    # Handle properties if they exist
                    props = el.get("properties", {})
                    for prop_name, prop_value in props.items():
                        text_parts.append(f"{prop_name}: {prop_value}")
                    
                    texts.append(" | ".join(text_parts))
                else:
                    texts.append(str(el))
            
            # Show texts in expanders
            st.write("### Text Descriptions")
            for i, text in enumerate(texts):
                with st.expander(f"Element {i+1}"):
                    st.write(text)

                # Generate embeddings button
                if openai_api_key and st.button("Generate Embeddings"):
                    try:
                        # Show progress bar
                        progress_bar = st.progress(0)
                        
                        # Generate embeddings with progress callback
                        embeddings = embedding_processor.generate_embeddings(
                            texts,
                            progress_callback=progress_bar.progress
                        )
                        
                        st.success(f"Embeddings generated using {selected_model}!")
                        st.session_state['embeddings_processor'] = embedding_processor
                        st.session_state['texts'] = texts
                    except Exception as e:
                        st.error(f"Error generating embeddings: {str(e)}")

# Chatbot section
if 'embeddings_processor' in st.session_state and 'texts' in st.session_state:
    st.header("Chat with your JSON")
    user_query = st.text_input("Ask a question about your data:")
    
    if user_query:
        try:
            embedding_processor = st.session_state['embeddings_processor']
            result = embedding_processor.find_most_similar(user_query)
            st.write("Most relevant element:")
            st.write(result['text'])
            st.write(f"Similarity score: {result['similarity_score']:.2f}")
        except Exception as e:
            st.error(f"Error processing query: {str(e)}")
