"""Streamlit interface for indexing and searching the RAG vector store."""

from pathlib import Path
import os
import sys
import time

import streamlit as st
import yaml
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI

# Add RAG directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "RAG"))

from rag_indexing import build_index
from audit_log import log_audit_event

load_dotenv()

st.set_page_config(page_title="RAG Search", layout="wide")

# Authentication
with open(Path(__file__).parent / 'config.yaml') as file:
    config = yaml.safe_load(file)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.name = None
    st.session_state.login_time = None

def check_credentials(username, password):
    """Check if credentials are valid"""
    if username in config['credentials']['usernames']:
        stored_password = config['credentials']['usernames'][username]['password']
        if stored_password == password:
            return True, config['credentials']['usernames'][username]['name']
    return False, None


def check_session_timeout(timeout_seconds: int = 1800) -> bool:
    """
    Check if session has timed out (default 30 minutes).
    Returns True if session is still valid, False if expired.
    """
    if not st.session_state.logged_in or not st.session_state.login_time:
        return True
    
    elapsed = time.time() - st.session_state.login_time
    
    if elapsed > timeout_seconds:
        st.session_state.logged_in = False
        st.session_state.login_time = None
        return False
    
    return True


# Login UI
if not st.session_state.logged_in:
    st.title("🔐 RAG Search Login")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Please log in")
        username = st.text_input("Username", key="username_input")
        password = st.text_input("Password", type="password", key="password_input")
        
        if st.button("Login", use_container_width=True, type="primary"):
            valid, user_name = check_credentials(username, password)
            if valid:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.name = user_name
                st.session_state.login_time = time.time()
                log_audit_event(username, "login", resource="rag_search")
                st.rerun()
            else:
                log_audit_event(username, "login_failed", resource="rag_search", status="failure")
                st.error("❌ Invalid username or password")
        
        st.divider()
        st.caption("Demo credentials: admin / admin123 or demo / demo123")
    st.stop()

# Check for session timeout
if not check_session_timeout():
    st.error("⏱️ Session expired. Please log in again.")
    st.stop()

st.title("Document Search & Chat")

index_path = Path("../faiss_index")
output_dir = Path("../data/output")


def index_exists() -> bool:
    return index_path.exists() and (index_path / "index.faiss").exists()


# Sidebar: User & Indexing
with st.sidebar:
    # User section
    st.write(f"👤 Welcome, **{st.session_state.name}**")
    if st.button("🚪 Logout", use_container_width=True):
        log_audit_event(st.session_state.username, "logout", resource="rag_search")
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.name = None
        st.rerun()
    
    st.divider()
    
    # Indexing section
    st.header("Indexing")
    
    available_files = sorted(output_dir.glob("*.json")) if output_dir.exists() else []
    file_labels = [file.name for file in available_files]
    
    if available_files:
        selected_labels = st.multiselect(
            "Select files to index",
            options=file_labels,
            default=file_labels,
        )
        selected_files = [output_dir / label for label in selected_labels]
        
        if st.button("Build/Refresh Index", disabled=not selected_files):
            with st.spinner("Building index..."):
                try:
                    build_index.build_index_for_files(selected_files)
                    st.cache_resource.clear()
                    st.success("✓ Index ready")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.info("No JSON files in ../data/output/")
    
    st.divider()
    status = "✓ Ready" if index_exists() else "✗ Missing"
    st.write(f"Status: {status}")


# Check if index exists
if not index_exists():
    st.warning("Build an index first using the sidebar.")
    st.stop()

# Load vectorstore
@st.cache_resource
def load_vectorstore():
    embeddings = OpenAIEmbeddings()
    return FAISS.load_local(
        str(index_path),
        embeddings,
        allow_dangerous_deserialization=True
    )

try:
    vectorstore = load_vectorstore()
except Exception as e:
    st.error(f"Failed to load index: {e}")
    st.stop()

# Search section
col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input(
        "Search",
        placeholder="e.g., 'receipts from Walmart' or 'payment info'"
    )
with col2:
    num_results = st.number_input("Results", min_value=1, max_value=20, value=5)

doc_type = st.selectbox(
    "Filter type",
    ["All", "receipt", "pay_stub", "bank_statement", "investment_statement"]
)

if query:
    with st.spinner("Searching..."):
        try:
            results = vectorstore.similarity_search_with_score(query, k=num_results*3)
            
            if doc_type != "All":
                results = [
                    (doc, score) for doc, score in results
                    if doc.metadata.get("document_type") == doc_type
                ][:num_results]
            else:
                results = results[:num_results]
            
            if results:
                st.subheader(f"{len(results)} result(s)")
                
                for idx, (doc, score) in enumerate(results, 1):
                    file_name = doc.metadata.get("file_name", "Unknown")
                    doc_type_meta = doc.metadata.get("document_type", "?")
                    confidence = doc.metadata.get("ocr_avg_confidence", "?")
                    
                    with st.expander(f"**{idx}. {file_name}** ({doc_type_meta}, score: {score:.3f})"):
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.caption("**Meta**")
                            st.write(f"Confidence: {confidence:.2f}" if confidence != "?" else "Confidence: ?")
                            if "chunk_index" in doc.metadata:
                                st.write(f"Chunk: {doc.metadata['chunk_index']+1}/{doc.metadata.get('total_chunks', '?')}")
                        with col2:
                            st.caption("**Content**")
                            st.text(doc.page_content[:500])
            else:
                st.info("No results found.")
        except Exception as e:
            st.error(f"Error: {e}")

# Chat section
st.divider()
st.header("Chat")

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message.get("sources"):
            st.caption("Sources: " + ", ".join(message["sources"]))

user_input = st.chat_input("Ask about your documents...")

if user_input:
    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.write(user_input)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Build context
                results = vectorstore.similarity_search_with_score(user_input, k=6)
                context = "\n\n".join([doc.page_content for doc, _ in results])
                sources = [f"{doc.metadata.get('file_name', '?')} ({score:.2f})" 
                          for doc, score in results]
                
                # Get answer
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                response = client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
                    messages=[
                        {"role": "system", "content": "Answer using only the provided context. If insufficient, say you don't know."},
                        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_input}"},
                    ],
                    temperature=0.2,
                )
                
                answer = response.choices[0].message.content.strip()
                st.write(answer)
                st.caption("Sources: " + ", ".join(sources))
                
                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": answer, "sources": sources}
                )
            except Exception as e:
                st.error(f"Error: {e}")
