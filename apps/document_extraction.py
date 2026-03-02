import json
from pathlib import Path
import sys
import hashlib
import time

import streamlit as st
import pymupdf
import numpy as np
from PIL import Image
import cv2
import easyocr
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "Document_Extraction"))

from src.config import get_openai_settings
from src.llm_extract import extract_key_values
from src.main import extract_document_text, format_markdown
from audit_log import log_audit_event

SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


def pdf_to_preview_image(pdf_path: Path) -> Image.Image:
    """Convert the first page of a PDF to a PIL Image for preview."""
    doc = pymupdf.open(str(pdf_path))
    page = doc[0]  # First page
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))  # 2x scale for better quality
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    doc.close()
    return img


def generate_ocr_visualization(file_path: Path, min_confidence: float = 0.0) -> tuple[Image.Image, list[dict]]:
    """Generate OCR visualization with bounding boxes and confidence scores for images or PDFs.
    
    Returns:
        Tuple of (visualization_image, ocr_details_list)
    """
    reader = easyocr.Reader(['en'], gpu=False)
    
    # Handle PDF - convert first page to image
    if file_path.suffix.lower() == ".pdf":
        doc = pymupdf.open(str(file_path))
        page = doc[0]
        pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:  # RGBA
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 1:  # Grayscale
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        doc.close()
    else:
        # Handle image files
        img = cv2.imread(str(file_path))
        if img is None:
            raise RuntimeError(f"Failed to load image: {file_path}")
    
    # Perform OCR
    results = reader.readtext(img)
    img_plot = img.copy()
    ocr_details = []
    
    # Draw bounding boxes and text labels with confidence scores
    for (box, text, confidence) in results:
        # Skip if below confidence threshold
        if confidence < min_confidence:
            continue
        
        pts = np.array(box, dtype=int)
        cv2.polylines(img_plot, [pts], True, (0, 255, 0), 2)
        x, y = pts[0]
        
        # Display text without confidence score
        cv2.putText(img_plot, text, (x, y - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        # Store OCR details
        ocr_details.append({
            'text': text,
            'confidence': confidence,
            'box': pts.tolist()
        })
    
    # Convert BGR to RGB for display
    img_rgb = cv2.cvtColor(img_plot, cv2.COLOR_BGR2RGB)
    return Image.fromarray(img_rgb), ocr_details


def list_supported_files(directory: Path) -> list[Path]:
    return sorted(
        [
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
    )


def load_extracted_documents(output_dir: Path) -> dict:
    """Load all extracted markdown documents from output directory."""
    documents = {}
    output_path = Path(output_dir)
    
    if not output_path.exists():
        return documents
    
    # Load markdown files for full text content
    for md_file in output_path.glob("*.md"):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                documents[md_file.stem] = f.read()
        except Exception as e:
            st.warning(f"Could not load {md_file.name}: {e}")
    
    return documents


def chunk_documents(documents: dict, chunk_size: int = 500) -> list[dict]:
    """Split documents into chunks for semantic search."""
    chunks = []
    
    for doc_name, content in documents.items():
        # Split by paragraphs first, then by characters if needed
        paragraphs = content.split('\n\n')
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append({
                        "text": current_chunk.strip(),
                        "source": doc_name
                    })
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append({
                "text": current_chunk.strip(),
                "source": doc_name
            })
    
    return chunks


def calculate_similarity(query: str, text: str) -> float:
    """Simple keyword-based similarity scoring."""
    query_words = set(query.lower().split())
    text_words = set(text.lower().split())
    
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'was', 'are', 'be'}
    query_words = query_words - stop_words
    text_words = text_words - stop_words
    
    if not query_words:
        return 0.0
    
    # Calculate overlap
    overlap = len(query_words & text_words)
    return overlap / len(query_words)


def search_relevant_chunks(documents: dict, query: str, top_k: int = 3) -> tuple[str, list[str]]:
    """Search for relevant document chunks using keyword similarity."""
    chunks = chunk_documents(documents, chunk_size=500)
    
    if not chunks:
        return "", []
    
    # Score all chunks
    scored_chunks = []
    for chunk in chunks:
        score = calculate_similarity(query, chunk["text"])
        if score > 0:  # Only include chunks with some match
            scored_chunks.append((score, chunk))
    
    # If no keyword matches, include all chunks
    if not scored_chunks:
        scored_chunks = [(0, chunk) for chunk in chunks]
    
    # Sort by score and get top K
    scored_chunks.sort(reverse=True, key=lambda x: x[0])
    top_chunks = scored_chunks[:top_k]
    
    # Build context from relevant chunks
    context = "Relevant documents found:\n\n"
    sources = set()
    
    for score, chunk in top_chunks:
        context += f"--- From {chunk['source']} (relevance: {score:.2f}) ---\n"
        context += chunk["text"] + "\n\n"
        sources.add(chunk['source'])
    
    return context, list(sources)


def query_documents_with_llm(api_key: str, model: str, documents: dict, query: str) -> tuple[str, list[str]]:
    """Query extracted documents using LLM with RAG-style chunk retrieval."""
    if not documents:
        return "No extracted documents found. Please extract documents first.", []
    
    # Search for relevant chunks instead of using all documents
    context, sources = search_relevant_chunks(documents, query, top_k=5)
    
    if not context:
        return "No relevant information found in documents.", []
    
    # Create the prompt for the LLM
    system_prompt = """You are a helpful assistant that answers questions based on extracted document information. 
    Answer questions using only the information provided in the document chunks below.
    If information is not available in the documents, say so clearly.
    Be concise and specific in your answers. Cite which document you found the information in."""
    
    user_message = f"""{context}

Based on the above extracted document information, please answer this question:
{query}"""
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        answer = response.choices[0].message.content
        return answer, sources
    except Exception as e:
        return f"Error querying documents: {str(e)}", []


def save_outputs(output_dir: Path, input_path: Path, result: dict, markdown: str) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{input_path.name}.json"
    md_path = output_dir / f"{input_path.name}.md"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    return json_path, md_path


st.set_page_config(page_title="Document Extraction", layout="wide")

# Load authentication config
with open('config.yaml') as file:
    config = yaml.safe_load(file)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.name = None
    st.session_state.login_time = None

def hash_password(password):
    """Simple password hashing for verification"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(username, password):
    """Check if credentials are valid"""
    if username in config['credentials']['usernames']:
        stored_password = config['credentials']['usernames'][username]['password']
        if stored_password == password:  # In production, use hashed passwords
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


# Login UI - show if not logged in
if not st.session_state.logged_in:
    st.title("🔐 Document Extraction Login")
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
                log_audit_event(username, "login", resource="document_extraction")
                st.rerun()
            else:
                log_audit_event(username, "login_failed", resource="document_extraction", status="failure")
                st.error("❌ Invalid username or password")
        
        st.divider()
        st.caption("Demo credentials: admin / admin123 or demo / demo123")
    st.stop()

# Check for session timeout
if not check_session_timeout():
    st.error("⏱️ Session expired. Please log in again.")
    st.stop()

# Logout button in sidebar (only shows when logged in)
with st.sidebar:
    st.write(f"👤 Welcome, **{st.session_state.name}**")
    if st.button("🚪 Logout", use_container_width=True):
        log_audit_event(st.session_state.username, "logout", resource="document_extraction")
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.name = None
        st.rerun()

if st.button("Reset"):
    for key in ["results", "errors", "last_directory"]:
        if key in st.session_state:
            del st.session_state[key]

st.header("Document Selection")

default_directory = st.session_state.get("last_directory", "../data/input")
directory_input = st.text_input("Documents directory path", value=default_directory)
use_schema = st.checkbox(
    "Use schema (pay_stub, bank_statement, investment_statement, receipt)",
    value=True,
)

if directory_input:
    directory = Path(directory_input)
    st.session_state["last_directory"] = str(directory)

    if directory.is_dir():
        files = list_supported_files(directory)
        st.caption(f"Found {len(files)} supported file(s).")

        if files:
            for path in files[:10]:
                st.write(f"- {path.name}")

        if st.button("Begin Extraction"):
            try:
                api_key, model = get_openai_settings()
            except RuntimeError as exc:
                st.error(str(exc))
            else:
                st.session_state["results"] = []
                st.session_state["errors"] = []

                output_dir = Path("../data/output")
                progress = st.progress(0.0)

                for index, path in enumerate(files, start=1):
                    try:
                        text = extract_document_text(path)
                        if not text:
                            raise RuntimeError("No text extracted from document.")
                        
                        # Generate OCR visualization and details first
                        try:
                            ocr_viz, ocr_details = generate_ocr_visualization(path)
                        except Exception as viz_error:
                            ocr_viz = None
                            ocr_details = []
                            print(f"Warning: Could not generate OCR visualization for {path.name}: {viz_error}")

                        result = extract_key_values(
                            api_key,
                            model,
                            text,
                            enforce_schema=use_schema,
                        )
                        
                        # Format markdown with OCR confidence scores
                        markdown = format_markdown(result, ocr_details=ocr_details)
                        json_path, md_path = save_outputs(output_dir, path, result, markdown)

                        st.session_state["results"].append(
                            {
                                "name": path.name,
                                "path": path,
                                "result": result,
                                "markdown": markdown,
                                "raw_text": text,
                                "json_path": json_path,
                                "md_path": md_path,
                                "ocr_viz": ocr_viz,
                                "ocr_details": ocr_details,
                            }
                        )
                    except Exception as exc:
                        st.session_state["errors"].append({"name": path.name, "error": str(exc)})

                    progress.progress(index / max(len(files), 1))
                
                st.success("Extraction complete.")
    else:
        st.warning("Directory not found.")

st.header("Results")

errors = st.session_state.get("errors", [])
if errors:
    st.subheader("Errors")
    for item in errors:
        st.write(f"- {item['name']}: {item['error']}")

results = st.session_state.get("results", [])
if not results:
    st.info("No results yet. Run extraction above.")
else:
    result_tabs = st.tabs([item["name"] for item in results])

    for tab, item in zip(result_tabs, results):
        with tab:
            st.subheader(item["name"])
            st.caption(f"Saved JSON: {item['json_path']}")
            st.caption(f"Saved Markdown: {item['md_path']}")

            # Two-column layout: Image on left, tabs on right
            col1, col2 = st.columns(2)
            
            with col1:
                if item["path"].suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    st.image(str(item["path"]), caption="Original Document", use_container_width=True)
                elif item["path"].suffix.lower() == ".pdf":
                    try:
                        pdf_image = pdf_to_preview_image(item["path"])
                        st.image(pdf_image, caption="PDF Preview (First Page)", use_container_width=True)
                    except Exception as e:
                        st.error(f"Could not generate PDF preview: {e}")
                else:
                    st.info("Preview not available")
            
            with col2:
                output_tabs = st.tabs(["Markdown", "JSON", "Raw OCR Output", "OCR Visualization"])
                
                with output_tabs[0]:
                    st.markdown(item["markdown"])
                
                with output_tabs[1]:
                    st.json(item["result"])
                
                with output_tabs[2]:
                    # Display raw OCR output with confidence scores
                    if item.get("ocr_details"):
                        st.caption("All detected text with confidence scores")
                        ocr_table = []
                        for idx, detail in enumerate(item["ocr_details"], 1):
                            # Color code by confidence
                            conf = detail['confidence']
                            if conf >= 0.8:
                                status = "🟢 High"
                            elif conf >= 0.5:
                                status = "🟡 Medium"
                            else:
                                status = "🔴 Low"
                            
                            ocr_table.append({
                                "#": idx,
                                "Text": detail['text'],
                                "Confidence": f"{conf:.3f}",
                                "Quality": status
                            })
                        st.dataframe(ocr_table, use_container_width=True, hide_index=True)
                    else:
                        # Fallback to line-based display
                        lines = item["raw_text"].split('\n')
                        ocr_table = [{"Line": i+1, "Text": line} for i, line in enumerate(lines)]
                        st.dataframe(ocr_table, use_container_width=True, hide_index=True)
                
                with output_tabs[3]:
                    if item.get("ocr_viz"):
                        st.image(item["ocr_viz"], caption="OCR Bounding Boxes", use_container_width=True)
                    else:
                        st.info("OCR visualization not available for this document")


# Chat Interface to Query Documents
st.divider()
st.header("💬 Chat with Your Documents")
st.write("Ask questions about extracted document information")

output_dir = Path("../data/output")
extracted_docs = load_extracted_documents(output_dir)

col1, col2 = st.columns([3, 1])

with col1:
    user_query = st.text_input("Ask a question about your documents:", placeholder="e.g., What is the total income across all documents?")

with col2:
    search_button = st.button("🔍 Search", use_container_width=True)

if search_button and user_query:
    try:
        api_key, model = get_openai_settings()
        answer, doc_sources = query_documents_with_llm(api_key, model, extracted_docs, user_query)
        
        st.info(f"**Question:** {user_query}")
        st.write(answer)
        
        if doc_sources:
            with st.expander("📄 Documents Referenced"):
                for doc in doc_sources:
                    st.write(f"- {doc}")
    
    except RuntimeError as exc:
        st.error(f"Configuration error: {str(exc)}")
    except Exception as exc:
        st.error(f"Error: {str(exc)}")
