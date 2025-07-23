import streamlit as st

class ChatTab:
    @staticmethod
    def render(embedding_processor):
        """Render the Chat tab."""
        st.subheader("💬 Chat with your Data")
        
        if 'embedding_processor' in st.session_state and st.session_state.embedding_processor.embeddings:
            if 'api_key' not in st.session_state:
                st.warning("Please set your OpenAI API key in the API Key tab first.")
            else:
                ChatTab._show_chat_interface(embedding_processor)
        else:
            st.warning("Please generate or load embeddings first before using the chat feature.")

    @staticmethod
    def _show_chat_interface(embedding_processor):
        """Show the chat interface."""
        st.write("Ask questions about your building elements:")
        user_query = st.text_input("Enter your question:", key="chat_query")
        
        if user_query:
            with st.spinner("Searching..."):
                try:
                    result = embedding_processor.find_most_similar(user_query)
                    st.write("Most relevant element:")
                    st.success(result['text'])
                    st.info(f"Similarity score: {result['similarity_score']:.2f}")
                except Exception as e:
                    st.error(f"Error processing query: {str(e)}")
