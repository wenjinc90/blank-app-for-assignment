import streamlit as st
import json
import openai
import numpy as np
import os
from utils.ifc_processing import IFCProcessor, check_ifcopenshell_installation, install_ifcopenshell_message

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
    # Add download button for processed IFC data
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
            
            st.download_button(
                label="📥 Download Processed Data as JSON",
                data=json_string,
                file_name=download_filename,
                mime="application/json",
                help="Download the processed IFC data in JSON format"
            )
        except Exception as e:
            st.error(f"Error preparing download: {e}")
    
    st.json(data)

    # Extract elements for embedding
    elements = data.get("elements", [])
    texts = []
    for el in elements:
        props = el.get("properties", {})
        text = f"{el.get('type', '')} {el.get('name', '')} " \
               f"Height: {props.get('OverallHeight', {}).get('value', '')} " \
               f"Width: {props.get('OverallWidth', {}).get('value', '')}"
        texts.append(text)

    # Show extracted texts
    st.write("Texts to embed:")
    for t in texts:
        st.write(t)

    # Embed using OpenAI (requires API key)
    openai_api_key = st.text_input("Enter your OpenAI API key:", type="password")
    if openai_api_key and st.button("Generate Embeddings"):
        openai.api_key = openai_api_key
        embeddings = []
        for t in texts:
            response = openai.embeddings.create(
                input=t,
                model="text-embedding-ada-002"
            )
            embeddings.append(response.data[0].embedding)
        st.success("Embeddings generated!")
        st.write(embeddings)
        st.session_state['embeddings'] = embeddings
        st.session_state['texts'] = texts

# Chatbot section
if 'embeddings' in st.session_state and 'texts' in st.session_state:
    st.header("Chat with your JSON")
    user_query = st.text_input("Ask a question about your data:")
    openai_api_key = st.session_state.get('openai_api_key', '')
    if user_query and openai_api_key:
        query_response = openai.embeddings.create(
            input=user_query,
            model="text-embedding-ada-002"
        )
        query_embedding = np.array(query_response.data[0].embedding)
        doc_embeddings = np.array(st.session_state['embeddings'])
        similarities = np.dot(doc_embeddings, query_embedding) / (
            np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding) + 1e-8
        )
        top_idx = int(np.argmax(similarities))
        st.write("Most relevant element:")
        st.write(st.session_state['texts'][top_idx])
