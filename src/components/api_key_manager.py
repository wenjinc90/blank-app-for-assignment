import streamlit as st

class APIKeyManager:
    @staticmethod
    def render(embedding_processor):
        """Render the API Key management tab."""
        st.subheader("🔑 OpenAI API Key")
        
        if 'embedding_processor' not in st.session_state:
            st.session_state.embedding_processor = embedding_processor
        
        st.write("Enter your API key once and it will be used across all features.")
        openai_api_key = st.text_input("Enter your OpenAI API key:", type="password")
        
        if st.session_state.get('api_key') != openai_api_key and openai_api_key:
            embedding_processor.set_api_key(openai_api_key)
            st.session_state.api_key = openai_api_key
            st.success("✅ API key set!")
