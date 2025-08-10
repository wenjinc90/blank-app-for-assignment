import streamlit as st
import openai
from typing import List, Dict, Any

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
        st.markdown("### 🔍 Building Element Search")
        
        # Add threshold slider
        threshold = st.slider(
            "Similarity Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.3,  # Default value lowered to 0.3
            step=0.01,
            help="Adjust this value to control how similar elements need to be to appear in results. Lower values will return more results."
        )
        
        # Initialize chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # Show chat history
        for message in st.session_state.chat_history:
            st.chat_message(message["role"]).write(message["content"])
        
        # Get user input
        user_query = st.chat_input("Ask about the building elements...")
        
        if user_query:
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_query
            })
            
            st.chat_message("user").write(user_query)
            
            with st.spinner("Thinking..."):
                try:
                    # Get initial results based on similarity
                    relevant_results = embedding_processor.find_similar_by_threshold(
                        user_query,
                        threshold=threshold
                    )
                    
                    # Filter results by type
                    filtered_results = ChatTab._filter_results_by_type(relevant_results, user_query)
                    
                    response = ChatTab._generate_chat_response(
                        user_query,
                        filtered_results,  # Pass filtered results to chat
                        st.session_state.get("api_key")
                    )
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response
                    })
                    
                    st.chat_message("assistant").write(response)
                    
                    # Show filtered search details
                    with st.expander("🔍 Search Details", expanded=False):
                        st.write(f"**Found {len(filtered_results)} relevant elements:**")
                        for i, result in enumerate(filtered_results, 1):
                            st.write(f"**{i}.** Score: {result['similarity_score']:.3f}")
                            # Show all data instead of just type, ID, and name
                            st.code(result['text'])  # Display the full text with all parameters

                except Exception as e:
                    error_msg = f"Error processing query: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_msg
                    })

    @staticmethod
    def _generate_chat_response(user_query, search_results, api_key):
        """Generate a conversational response using OpenAI Chat API."""
        if not api_key:
            st.error("API key not found. Please set your OpenAI API key first.")
            return "API key not found. Please set your OpenAI API key first."
        
        # Debug info
        st.write("🔍 Debug Info:")
        st.write("API Key present:", bool(api_key))
        with st.expander("Raw search results"):
            st.json(search_results)
        
        # Set up OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Create context from search results with simplified information
        if isinstance(search_results, list):
            # Multiple results
            context_parts = []
            for i, result in enumerate(search_results, 1):
                # Extract only type, ID, and name from the full text
                text = result['text']
                element_type = ""
                element_id = ""
                element_name = ""
                
                # Parse the text to extract key information
                parts = text.split(" | ")
                for part in parts:
                    if "Element Type:" in part:
                        element_type = part
                    elif "ID:" in part:
                        element_id = part
                    elif "Name:" in part:
                        element_name = part
                
                # Create simplified context
                simplified_text = f"{element_type} | {element_id} | {element_name}".strip(" | ")
                context_parts.append(f"Element {i} (Similarity: {result['similarity_score']:.2f}): {simplified_text}")
            
            context = "\n\n".join(context_parts)
            best_score = search_results[0]['similarity_score'] if search_results else 0
        else:
            # Single result (backward compatibility)
            text = search_results['text']
            parts = text.split(" | ")
            simplified_parts = [p for p in parts if any(key in p for key in ["Element Type:", "ID:", "Name:"])]
            simplified_text = " | ".join(simplified_parts)
            context = f"Element Details: {simplified_text}"
            best_score = search_results['similarity_score']
        
        # Create system prompt
        system_prompt = """You are an expert building information assistant specializing in explaining building elements from IFC files in a natural, conversational way.

CRITICAL INSTRUCTION: You must NEVER return data in the raw format with | symbols. Your job is to transform technical data into natural, easy-to-understand explanations.

Examples of how to respond:
BAD: "Wall | Material: Concrete | Thickness: 200mm | Fire Rating: 2 hours"
GOOD: "I found a concrete wall in the building. It's 200mm thick and has a fire rating of 2 hours."

BAD: "Door | Width: 900mm | Height: 2100mm | Material: Wood"
GOOD: "There's a wooden door that's 900mm wide and 2.1 meters tall."

When answering:
1. NEVER return the raw data format with | symbols
2. Always write complete, natural sentences
3. Explain technical details in simple, user-friendly language
4. If the similarity score is low (< 0.5), mention that the match might not be perfect
5. If multiple elements are provided, focus on the most relevant ones but mention if there are others
6. Extract and explain key information like:
   - What type of element it is
   - What it's made of
   - Its dimensions and properties
7. Be helpful and offer to provide more details if needed
8. Use a friendly, professional tone
9. Start responses with a natural opening like "I found..." or "Based on the data..."

Remember: Your role is to interpret and explain the data, not to display it in its raw form."""
        
        try:
            # Format the messages for better clarity
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""Question: {user_query}

Building Information:
{context}

Please provide a natural, conversational response that explains the relevant building elements."""}
            ]
            
            # Print debug info about the API call
            st.write("Making OpenAI API call...")
            with st.expander("Request Details", expanded=True):
                st.write("Messages being sent to OpenAI:")
                st.json(messages)
            
            # Make the API call
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=800,  # Increased for more detailed responses
                temperature=0.7,
                presence_penalty=0.6,  # Encourage more creative responses
                frequency_penalty=0.2  # Reduce repetition
            )
            
            generated_response = response.choices[0].message.content
            
            # Debug: Show the raw API response
            with st.expander("API Response Debug"):
                st.write("Raw API Response:")
                st.json({"response": generated_response})
            
            # Add confidence note if similarity is low
            if best_score < 0.5:
                generated_response += f"\n\n*Note: The similarity score is {best_score:.2f}, which suggests this might not be a perfect match for your question. You might want to try rephrasing your query.*"
            
            return generated_response
            
        except Exception as e:
            fallback_text = context if isinstance(search_results, str) else search_results[0]['text'] if search_results else "No data found"
            return f"Error generating response: {str(e)}. Here's the raw data I found: {fallback_text}"
    
    @staticmethod
    def _filter_results_by_type(results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Filter results to only show elements of the requested type."""
        # Map common terms to IFC types
        type_mapping = {
            'door': 'IfcDoor',
            'wall': 'IfcWall',
            'window': 'IfcWindow',
            'slab': 'IfcSlab',
            'beam': 'IfcBeam',
            'column': 'IfcColumn',
            'stair': 'IfcStair',
            'roof': 'IfcRoof',
            'curtain wall': 'IfcCurtainWall'
        }
        
        # Find requested type from query
        query_lower = query.lower()
        requested_type = None
        for term, ifc_type in type_mapping.items():
            if term in query_lower:
                requested_type = ifc_type
                break
        
        if not requested_type:
            return results  # Return all results if no specific type requested
        
        # Filter results to only include elements of the requested type
        filtered_results = [
            result for result in results 
            if requested_type in result['text'].split(' | ')[0]  # Check first part which contains Element Type
        ]
        
        return filtered_results

