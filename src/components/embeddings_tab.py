import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.manifold import TSNE
import os

class EmbeddingsTab:
    @staticmethod
    def render(embedding_processor):
        """Render the Generate & Manage Embeddings tab."""
        if 'api_key' not in st.session_state:
            st.warning("Please set your OpenAI API key in the API Key tab first.")
            return
            
        # Add model selection
        embedding_models = embedding_processor.get_available_models()
        selected_model = st.selectbox(
            "Select Embedding Model:",
            list(embedding_models.keys()),
            index=0,
            help="Choose the OpenAI embedding model to use"
        )
        st.info(f"Model Info: {embedding_models[selected_model]}")
        
        return selected_model

    @staticmethod
    def process_and_generate(texts, embedding_processor, selected_model, openai_api_key):
        """Process texts and generate embeddings."""
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
                    
                    EmbeddingsTab._handle_save_options(embedding_processor)
                    EmbeddingsTab._show_query_section(embedding_processor)
                    
            except Exception as e:
                st.error(f"Error generating embeddings: {str(e)}")

    @staticmethod
    def _handle_save_options(embedding_processor):
        """Handle embedding save options."""
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

    @staticmethod
    def _show_query_section(embedding_processor):
        """Show the query section for embeddings."""
        st.write("### 🔍 Query Your Data")
        st.write("Ask questions about your building elements:")
        user_query = st.text_input("Enter your question:")
        if user_query:
            with st.spinner("Searching..."):
                result = embedding_processor.find_most_similar(user_query)
                st.write("Most relevant element:")
                st.success(result['text'])
                st.info(f"Similarity score: {result['similarity_score']:.2f}")

    @staticmethod
    def show_text_descriptions(texts):
        """Show text descriptions for embeddings."""
        st.write("### Text Descriptions")
        st.write("Below are the text descriptions that will be used for embeddings. Each description includes all available properties of the building element.")
        
        for i, text in enumerate(texts):
            with st.expander(f"Element {i+1}"):
                st.write(text)
