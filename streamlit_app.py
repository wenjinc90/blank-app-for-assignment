import streamlit as st
import json
import openai
import numpy as np

st.title("🎈 My new app")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)

# JSON file uploader
uploaded_file = st.file_uploader("Upload a JSON file", type=["json"])
if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        st.success("JSON file uploaded successfully!")
        st.json(data)

        # Extract elements for embedding
        elements = data.get("elements", [])
        texts = []
        for el in elements:
            # You can customize what text to embed; here we use type, name, and properties
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

    except Exception as e:
        st.error(f"Error reading JSON file: {e}")

# Chatbot section
if 'embeddings' in st.session_state and 'texts' in st.session_state:
    st.header("Chat with your JSON")
    user_query = st.text_input("Ask a question about your data:")
    if user_query and openai_api_key:
        # Embed the user query
        query_response = openai.embeddings.create(
            input=user_query,
            model="text-embedding-ada-002"
        )
        query_embedding = np.array(query_response.data[0].embedding)

        # Compute cosine similarity
        doc_embeddings = np.array(st.session_state['embeddings'])
        similarities = np.dot(doc_embeddings, query_embedding) / (
            np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding) + 1e-8
        )
        top_idx = int(np.argmax(similarities))
        st.write("Most relevant element:")
        st.write(st.session_state['texts'][top_idx])
