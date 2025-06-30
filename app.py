import streamlit as st
import tempfile
import os
from config import Config
from vectorstore import VectorStore
from llm_manager import LLMManager

# Page configuration
st.set_page_config(
    page_title="Markdown Chat Assistant",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "file_loaded" not in st.session_state:
    st.session_state.file_loaded = False

# Title and description
st.title("📄 Markdown Chat Assistant")
st.markdown("Upload a Markdown file and chat with its contents using RAG!")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # File upload
    uploaded_file = st.file_uploader("Choose a Markdown file", type=['md'])
    
    # Model selection
    model_choice = st.selectbox(
        "Select Model",
        ["OpenAI GPT", "Google Gemini", "GitHub Models", "LM Studio (Local)"]
    )
    
    # Advanced settings
    with st.expander("Advanced Settings"):
        chunk_size = st.slider("Chunk Size", 100, 1000, Config.CHUNK_SIZE)
        chunk_overlap = st.slider("Chunk Overlap", 0, 100, Config.CHUNK_OVERLAP)
        top_k = st.slider("Top K Chunks", 1, 10, Config.TOP_K_CHUNKS)
    
    # Process file button
    if uploaded_file and st.button("Process File", type="primary"):
        with st.spinner("Processing file..."):
            # Read file content
            content = uploaded_file.read().decode("utf-8")
            
            # Initialize vector store
            vector_store = VectorStore(Config.EMBEDDING_MODEL)
            
            # Build index
            try:
                vector_store.build_index(content, chunk_size, chunk_overlap)
                st.session_state.vector_store = vector_store
                st.session_state.file_loaded = True
                st.session_state.messages = []  # Clear previous messages
                st.success(f"✅ Processed {len(vector_store.chunks)} chunks from {uploaded_file.name}")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
    
    # Display current status
    if st.session_state.file_loaded:
        st.success("📄 File loaded and indexed")
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    else:
        st.info("👆 Please upload a Markdown file")

# Main chat interface
if st.session_state.file_loaded:
    # Initialize LLM manager
    llm_manager = LLMManager()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about the document"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Retrieve relevant chunks
                results = st.session_state.vector_store.search(prompt, top_k)
                
                # Build context from retrieved chunks
                context = "\n\n---\n\n".join([chunk for chunk, _ in results])
                
                # System prompt
                system_prompt = """You are a helpful assistant that answers questions based on the provided context from a Markdown document. 
                Always base your answers on the context provided. If the answer cannot be found in the context, say so clearly.
                Be concise but thorough in your responses."""
                
                # Generate response
                response = llm_manager.generate_response(
                    model_choice,
                    system_prompt,
                    context,
                    prompt
                )
                
                # Display response
                st.markdown(response)
                
                # Add to message history
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Show retrieved chunks in expander
                with st.expander("📚 Retrieved Context"):
                    for i, (chunk, distance) in enumerate(results):
                        st.markdown(f"**Chunk {i+1}** (distance: {distance:.2f})")
                        st.markdown(chunk)
                        st.markdown("---")
else:
    # Welcome message
    st.info("👈 Please upload a Markdown file from the sidebar to start chatting!")
    
    # Show example
    with st.expander("📖 How to use"):
        st.markdown("""
        1. **Upload a Markdown file** using the sidebar
        2. **Select your preferred model** (OpenAI, Gemini, GitHub Models, or local LM Studio)
        3. **Click "Process File"** to index the document
        4. **Start chatting** with your document!
        
        The app will:
        - Split your document into chunks
        - Create embeddings for semantic search
        - Retrieve relevant context for each question
        - Generate answers using your selected model
        """)