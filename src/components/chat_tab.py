import streamlit as st
import openai

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
        # Clear chat button
        col1, col2 = st.columns([6, 1])
        with col1:
            st.write("Ask questions about your building elements:")
        with col2:
            if st.button("Clear Chat", type="secondary"):
                st.session_state.chat_history = []
                st.rerun()
        
        # Initialize chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Display chat history
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.chat_message("user").write(message['content'])
            else:
                st.chat_message("assistant").write(message['content'])
        
        # User input
        user_query = st.chat_input("Enter your question:")
        
        if user_query:
            # Add user message to history
            st.session_state.chat_history.append({
                'role': 'user',
                'content': user_query
            })
            
            # Display user message
            st.chat_message("user").write(user_query)
            
            with st.spinner("Thinking..."):
                try:
                    # Find top 3 relevant building elements for better context
                    top_results = embedding_processor.find_top_similar(user_query, top_k=3)
                    
                    # Generate conversational response using OpenAI Chat API
                    response = ChatTab._generate_chat_response(
                        user_query, 
                        top_results, 
                        st.session_state.get('api_key')
                    )
                    
                    # Add assistant response to history
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': response
                    })
                    
                    # Display assistant response
                    st.chat_message("assistant").write(response)
                    
                    # Show expandable section with detailed search results
                    with st.expander("🔍 Search Details", expanded=False):
                        st.write("**Top matching elements:**")
                        for i, result in enumerate(top_results, 1):
                            st.write(f"**{i}.** Score: {result['similarity_score']:.3f}")
                            st.code(result['text'], language=None)
                    
                except Exception as e:
                    error_msg = f"Error processing query: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': error_msg
                    })
    
    @staticmethod
    def _generate_chat_response(user_query, search_results, api_key):
        """Generate a conversational response using OpenAI Chat API."""
        if not api_key:
            return "API key not found. Please set your OpenAI API key first."
        
        # Set up OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Create context from search results
        if isinstance(search_results, list):
            # Multiple results
            context_parts = []
            for i, result in enumerate(search_results, 1):
                context_parts.append(f"Element {i} (Similarity: {result['similarity_score']:.2f}): {result['text']}")
            context = "\n\n".join(context_parts)
            best_score = search_results[0]['similarity_score'] if search_results else 0
        else:
            # Single result (backward compatibility)
            context = f"Element Details: {search_results['text']}"
            best_score = search_results['similarity_score']
        
        # Create system prompt
        system_prompt = """You are a helpful building information assistant. You help users understand their building data by providing clear, conversational responses about building elements from IFC files.

When answering:
1. Provide natural, conversational responses
2. Explain technical details in user-friendly language
3. If the similarity score is low (< 0.5), mention that the match might not be perfect
4. If multiple elements are provided, focus on the most relevant ones but mention if there are others
5. Extract key information like element type, materials, dimensions, and properties
6. Be helpful and offer to provide more details if needed
7. Use a friendly, professional tone

The building element data contains information like element type, ID, name, materials, dimensions, and various properties separated by | symbols."""
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User Question: {user_query}\n\nRelevant Building Element Data:\n{context}"}
                ],
                max_tokens=600,
                temperature=0.7
            )
            
            generated_response = response.choices[0].message.content
            
            # Add confidence note if similarity is low
            if best_score < 0.5:
                generated_response += f"\n\n*Note: The similarity score is {best_score:.2f}, which suggests this might not be a perfect match for your question. You might want to try rephrasing your query.*"
            
            return generated_response
            
        except Exception as e:
            fallback_text = context if isinstance(search_results, str) else search_results[0]['text'] if search_results else "No data found"
            return f"Error generating response: {str(e)}. Here's the raw data I found: {fallback_text}"
