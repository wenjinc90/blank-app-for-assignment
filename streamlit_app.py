import streamlit as st
from src.utils.file_loader import FileLoader
from src.utils.embedding import EmbeddingProcessor
from src.utils.ifc_processing import IFCProcessor, check_ifcopenshell_installation, install_ifcopenshell_message
from src.components.api_key_manager import APIKeyManager
from src.components.overview_tab import OverviewTab
from src.components.elements_tab import ElementsTab
from src.components.download_tab import DownloadTab
from src.components.embeddings_tab import EmbeddingsTab
from src.components.load_embeddings_tab import LoadEmbeddingsTab
from src.components.chat_tab import ChatTab

def main():
    st.title("🎈 IFC File Processor")
    st.write(
        "Process and analyze IFC files with ease. Upload your IFC file or use a sample model to get started."
    )

    # Initialize file loader
    sample_models_dir = "sample_models"
    sample_files = FileLoader.list_sample_models(sample_models_dir)

    # File selection
    selected_sample = st.selectbox(
        "Or select a sample model:",
        ["None"] + sample_files
    )

    # JSON/IFC file uploader
    uploaded_file = st.file_uploader("Upload a JSON or IFC file", type=["json", "ifc"])

    # Load data
    data = None
    if selected_sample != "None":
        sample_file_path = f"{sample_models_dir}/{selected_sample}"
        data = FileLoader.load_sample_file(sample_file_path)
    elif uploaded_file is not None:
        data = FileLoader.load_uploaded_file(uploaded_file)

    if data:
        # Initialize embedding processor
        if 'embedding_processor' not in st.session_state:
            st.session_state.embedding_processor = EmbeddingProcessor()
        embedding_processor = st.session_state.embedding_processor

        # Create tabs
        tab_names = ["Overview", "Building Elements", "Download", "API Key", 
                    "Generate Embeddings", "Load Embeddings", "Chat"]
        tab_overview, tab_elements, tab_download, tab_api, tab_embeddings, \
        tab_load, tab_chat = st.tabs(tab_names)

        # Render each tab
        with tab_overview:
            OverviewTab.render(data)

        with tab_elements:
            ElementsTab.render(data)

        with tab_download:
            DownloadTab.render(data)

        with tab_api:
            APIKeyManager.render(embedding_processor)

        with tab_embeddings:
            st.subheader("Generate & Manage Embeddings")
            selected_model = EmbeddingsTab.render(embedding_processor)
            
            # Process texts for embedding
            texts = []
            if data.get('file_info', {}).get('type') == 'IFC':
                processor = IFCProcessor()
                texts = processor.convert_to_text_chunks(data)
                st.write(f"Found {len(texts)} elements to process")
                
            EmbeddingsTab.process_and_generate(
                texts, 
                embedding_processor, 
                selected_model,
                st.session_state.get('api_key')
            )
            
            if texts:
                EmbeddingsTab.show_text_descriptions(texts)

        with tab_load:
            LoadEmbeddingsTab.render(embedding_processor)

        with tab_chat:
            ChatTab.render(embedding_processor)

if __name__ == "__main__":
    main()
            # For IFC files
