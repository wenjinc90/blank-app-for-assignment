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
    tab_overview, tab_elements, tab_download, tab_api, tab_embeddings, tab_load, tab_chat = st.tabs([
        "Overview", "Building Elements", "Download", "API Key", "Generate Embeddings", "Load Embeddings", "Chat"
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
    # API Key tab
    with tab_api:
        st.subheader("🔑 OpenAI API Key")
        
        # Initialize embedding processor
        if 'embedding_processor' not in st.session_state:
            st.session_state.embedding_processor = EmbeddingProcessor()
        
        embedding_processor = st.session_state.embedding_processor
        
        st.write("Enter your API key once and it will be used across all features.")
        openai_api_key = st.text_input("Enter your OpenAI API key:", type="password")
        if st.session_state.get('api_key') != openai_api_key and openai_api_key:
            embedding_processor.set_api_key(openai_api_key)
            st.session_state.api_key = openai_api_key
            st.success("✅ API key set!")
            
    with tab_embeddings:
        st.subheader("Generate & Manage Embeddings")
        
        if 'api_key' not in st.session_state:
            st.warning("Please set your OpenAI API key in the API Key tab first.")
            st.stop()
            
        # Add model selection
        embedding_models = embedding_processor.get_available_models()
        selected_model = st.selectbox(
            "Select Embedding Model:",
            list(embedding_models.keys()),
            index=0,
            help="Choose the OpenAI embedding model to use"
        )
        st.info(f"Model Info: {embedding_models[selected_model]}")
        
        # Process texts for embedding
        texts = []
        if data.get('file_info', {}).get('type') == 'IFC':
            processor = IFCProcessor()
            texts = processor.convert_to_text_chunks(data)
            st.write(f"Found {len(texts)} elements to process")
            
        # Generate embeddings button
        if texts and openai_api_key and st.button("🚀 Generate Embeddings"):
            try:
                with st.spinner("Generating embeddings..."):
                    progress_bar = st.progress(0)
                    embeddings = embedding_processor.generate_embeddings(
                        texts,
                        progress_callback=progress_bar.progress
                    )
                    st.session_state['texts'] = texts
                    st.success(f"✨ Generated {len(embeddings)} embeddings using {selected_model}!")
                    
                    # Add save options after generation
                    st.write("### Save Embeddings")
                    save_format = st.selectbox("Choose Format", ["pickle", "json"])
                    if st.button("💾 Save Embeddings"):
                        save_path = f"embeddings.{save_format}"
                        embedding_processor.save_embeddings(save_path, format=save_format)
                        with open(save_path, 'rb') as f:
                            st.download_button(
                                "📥 Download Embeddings",
                                f,
                                file_name=f"embeddings.{save_format}",
                                mime="application/octet-stream"
                            )
                        os.remove(save_path)
                    
                    # Add query section right after generation
                    st.write("### 🔍 Query Your Data")
                    st.write("Ask questions about your building elements:")
                    user_query = st.text_input("Enter your question:")
                    if user_query:
                        with st.spinner("Searching..."):
                            result = embedding_processor.find_most_similar(user_query)
                            st.write("Most relevant element:")
                            st.success(result['text'])
                            st.info(f"Similarity score: {result['similarity_score']:.2f}")
                    
            except Exception as e:
                st.error(f"Error generating embeddings: {str(e)}")
        
        # Add the Load Embeddings tab content
    with tab_load:
        st.subheader("Load Existing Embeddings")
        
        # Initialize embedding processor if not already done
        if 'embedding_processor' not in st.session_state:
            st.session_state.embedding_processor = EmbeddingProcessor()
        embedding_processor = st.session_state.embedding_processor
        
        if 'api_key' not in st.session_state:
            st.warning("Please set your OpenAI API key in the Settings tab first.")
            st.stop()
            
        uploaded_file = st.file_uploader("Upload saved embeddings", type=['pickle', 'json'])
        if uploaded_file:
            format_type = "pickle" if uploaded_file.name.endswith('.pickle') else "json"
            if st.button("📤 Load Embeddings"):
                try:
                    with st.spinner("Loading embeddings..."):
                        # Save uploaded file temporarily
                        with open('temp_embeddings', 'wb') as f:
                            f.write(uploaded_file.getvalue())
                        # Load embeddings
                        embedding_processor.load_embeddings('temp_embeddings', format=format_type)
                        # Clean up
                        os.remove('temp_embeddings')
                        st.success(f"✨ Loaded {len(embedding_processor.embeddings)} embeddings successfully!")
                        
                        # Show query interface after successful load
                        st.write("### 🔍 Query Your Data")
                        st.write("Ask questions about your building elements:")
                        user_query = st.text_input("Enter your question:", key="query_load")
                        if user_query:
                            with st.spinner("Searching..."):
                                result = embedding_processor.find_most_similar(user_query)
                                st.write("Most relevant element:")
                                st.success(result['text'])
                                st.info(f"Similarity score: {result['similarity_score']:.2f}")
                except Exception as e:
                    st.error(f"Error loading embeddings: {str(e)}")
        
        if embedding_processor.embeddings:
            st.info(f"📊 Current embeddings: {len(embedding_processor.embeddings)} vectors of dimension {len(embedding_processor.embeddings[0]) if embedding_processor.embeddings else 0}")
            
            # Add visualization options
            st.write("### 📈 Visualize Embeddings")
            viz_type = st.selectbox("Choose Visualization Method", ["2D Plot", "3D Plot", "Similarity Matrix"])
            
            import numpy as np
            import plotly.express as px
            import plotly.graph_objects as go
            from sklearn.manifold import TSNE
            
            embeddings_array = np.array(embedding_processor.embeddings)
            
            # Compute similarity matrix for both visualization and statistics
            with st.spinner("Computing similarity matrix..."):
                # Compute cosine similarity matrix
                similarity_matrix = np.dot(embeddings_array, embeddings_array.T)
                norms = np.linalg.norm(embeddings_array, axis=1)
                similarity_matrix /= np.outer(norms, norms)
            
            if viz_type in ["2D Plot", "3D Plot"]:
                n_components = 3 if viz_type == "3D Plot" else 2
                with st.spinner("Reducing dimensionality..."):
                    tsne = TSNE(n_components=n_components, random_state=42)
                    embeddings_reduced = tsne.fit_transform(embeddings_array)
                
                if viz_type == "2D Plot":
                    fig = px.scatter(
                        x=embeddings_reduced[:, 0],
                        y=embeddings_reduced[:, 1],
                        hover_name=[f"Element {i+1}" for i in range(len(embedding_processor.texts))],
                        title="2D Visualization of Embeddings"
                    )
                else:
                    fig = px.scatter_3d(
                        x=embeddings_reduced[:, 0],
                        y=embeddings_reduced[:, 1],
                        z=embeddings_reduced[:, 2],
                        hover_name=[f"Element {i+1}" for i in range(len(embedding_processor.texts))],
                        title="3D Visualization of Embeddings"
                    )
            
            else:  # Similarity Matrix
                fig = px.imshow(
                        similarity_matrix,
                        title="Similarity Matrix of Embeddings",
                        labels=dict(color="Cosine Similarity"),
                        color_continuous_scale="RdBu"
                    )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show statistics about the embeddings
            st.write("### 📊 Embedding Statistics")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Number of Embeddings", len(embedding_processor.embeddings))
                st.metric("Vector Dimension", len(embedding_processor.embeddings[0]))
            with col2:
                similarity_stats = {
                    "Min Similarity": np.min(similarity_matrix[np.triu_indices(len(similarity_matrix), k=1)]),
                    "Max Similarity": np.max(similarity_matrix[np.triu_indices(len(similarity_matrix), k=1)]),
                    "Avg Similarity": np.mean(similarity_matrix[np.triu_indices(len(similarity_matrix), k=1)])
                }
                for label, value in similarity_stats.items():
                    st.metric(label, f"{value:.3f}")
                    
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

                # Create columns for different actions
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Generate & Save")
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
                            
                            st.success(f"Generated {len(embeddings)} embeddings using {selected_model}!")
                            st.session_state['texts'] = texts
                            
                            # Add save option after generation
                            save_format = st.selectbox("Save Format", ["pickle", "json"])
                            if st.button("Save Embeddings"):
                                save_path = f"embeddings.{save_format}"
                                embedding_processor.save_embeddings(save_path, format=save_format)
                                with open(save_path, 'rb') as f:
                                    st.download_button(
                                        "Download Embeddings",
                                        f,
                                        file_name=f"embeddings.{save_format}",
                                        mime="application/octet-stream"
                                    )
                                os.remove(save_path)  # Clean up the temporary file
                        except Exception as e:
                            st.error(f"Error generating embeddings: {str(e)}")
                
                with col2:
                    st.subheader("Load Existing")
                    uploaded_file = st.file_uploader("Upload embeddings file", type=['pickle', 'json'])
                    if uploaded_file:
                        format_type = "pickle" if uploaded_file.name.endswith('.pickle') else "json"
                        if st.button("Load Embeddings"):
                            try:
                                # Save uploaded file temporarily
                                with open('temp_embeddings', 'wb') as f:
                                    f.write(uploaded_file.getvalue())
                                # Load embeddings
                                embedding_processor.load_embeddings('temp_embeddings', format=format_type)
                                # Clean up
                                os.remove('temp_embeddings')
                                st.success(f"Loaded {len(embedding_processor.embeddings)} embeddings successfully!")
                            except Exception as e:
                                st.error(f"Error loading embeddings: {str(e)}")

                # Show embedding stats if available
                if embedding_processor.embeddings:
                    st.info(f"Current embeddings: {len(embedding_processor.embeddings)} vectors of dimension {len(embedding_processor.embeddings[0]) if embedding_processor.embeddings else 0}")

    # Chat tab
    with tab_chat:
        st.subheader("💬 Chat with your Data")
        if 'embedding_processor' in st.session_state and st.session_state.embedding_processor.embeddings:
            if 'api_key' not in st.session_state:
                st.warning("Please set your OpenAI API key in the API Key tab first.")
            else:
                st.write("Ask questions about your building elements:")
                user_query = st.text_input("Enter your question:", key="chat_query")
                
                if user_query:
                    embedding_processor = st.session_state['embedding_processor']
                    with st.spinner("Searching..."):
                        try:
                            result = embedding_processor.find_most_similar(user_query)
                            st.write("Most relevant element:")
                            st.success(result['text'])
                            st.info(f"Similarity score: {result['similarity_score']:.2f}")
                        except Exception as e:
                            st.error(f"Error processing query: {str(e)}")
        else:
            st.warning("Please generate or load embeddings first before using the chat feature.")