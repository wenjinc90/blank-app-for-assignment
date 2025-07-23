import streamlit as st
import os
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.manifold import TSNE

class LoadEmbeddingsTab:
    @staticmethod
    def render(embedding_processor):
        """Render the Load Embeddings tab."""
        st.subheader("Load Existing Embeddings")
        
        if 'embedding_processor' not in st.session_state:
            st.session_state.embedding_processor = embedding_processor
        
        if 'api_key' not in st.session_state:
            st.warning("Please set your OpenAI API key in the Settings tab first.")
            return
            
        LoadEmbeddingsTab._handle_file_upload(embedding_processor)
        
        if embedding_processor.embeddings:
            LoadEmbeddingsTab._show_embeddings_info(embedding_processor)
            LoadEmbeddingsTab._show_visualization_options(embedding_processor)

    @staticmethod
    def _handle_file_upload(embedding_processor):
        """Handle embedding file upload."""
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
                        
                        LoadEmbeddingsTab._show_query_interface(embedding_processor)
                except Exception as e:
                    st.error(f"Error loading embeddings: {str(e)}")

    @staticmethod
    def _show_query_interface(embedding_processor):
        """Show query interface for loaded embeddings."""
        st.write("### 🔍 Query Your Data")
        st.write("Ask questions about your building elements:")
        user_query = st.text_input("Enter your question:", key="query_load")
        if user_query:
            with st.spinner("Searching..."):
                result = embedding_processor.find_most_similar(user_query)
                st.write("Most relevant element:")
                st.success(result['text'])
                st.info(f"Similarity score: {result['similarity_score']:.2f}")

    @staticmethod
    def _show_embeddings_info(embedding_processor):
        """Show information about current embeddings."""
        st.info(f"📊 Current embeddings: {len(embedding_processor.embeddings)} vectors of dimension {len(embedding_processor.embeddings[0]) if embedding_processor.embeddings else 0}")

    @staticmethod
    def _show_visualization_options(embedding_processor):
        """Show visualization options for embeddings."""
        import numpy as np
        import plotly.express as px
        from sklearn.manifold import TSNE

        st.write("### 📈 Visualize Embeddings")
        viz_type = st.selectbox("Choose Visualization Method", ["2D Plot", "3D Plot", "Similarity Matrix"])
        
        embeddings_array = np.array(embedding_processor.embeddings)
        
        # Compute similarity matrix
        with st.spinner("Computing similarity matrix..."):
            similarity_matrix = np.dot(embeddings_array, embeddings_array.T)
            norms = np.linalg.norm(embeddings_array, axis=1)
            similarity_matrix /= np.outer(norms, norms)
        
        if viz_type in ["2D Plot", "3D Plot"]:
            LoadEmbeddingsTab._show_dimensional_plot(embeddings_array, embedding_processor.texts, viz_type)
        else:
            LoadEmbeddingsTab._show_similarity_matrix(similarity_matrix)
        
        LoadEmbeddingsTab._show_statistics(similarity_matrix, embedding_processor)

    @staticmethod
    def _show_dimensional_plot(embeddings_array, texts, viz_type):
        """Show 2D or 3D plot of embeddings."""
        n_components = 3 if viz_type == "3D Plot" else 2
        with st.spinner("Reducing dimensionality..."):
            tsne = TSNE(n_components=n_components, random_state=42)
            embeddings_reduced = tsne.fit_transform(embeddings_array)
        
        if viz_type == "2D Plot":
            fig = px.scatter(
                x=embeddings_reduced[:, 0],
                y=embeddings_reduced[:, 1],
                hover_name=[f"Element {i+1}" for i in range(len(texts))],
                title="2D Visualization of Embeddings"
            )
        else:
            fig = px.scatter_3d(
                x=embeddings_reduced[:, 0],
                y=embeddings_reduced[:, 1],
                z=embeddings_reduced[:, 2],
                hover_name=[f"Element {i+1}" for i in range(len(texts))],
                title="3D Visualization of Embeddings"
            )
        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def _show_similarity_matrix(similarity_matrix):
        """Show similarity matrix visualization."""
        fig = px.imshow(
            similarity_matrix,
            title="Similarity Matrix of Embeddings",
            labels=dict(color="Cosine Similarity"),
            color_continuous_scale="RdBu"
        )
        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def _show_statistics(similarity_matrix, embedding_processor):
        """Show statistics about embeddings."""
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
