from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


def build_vectorstore(documents, save_path="faiss_index"):
    """Build vector store and save to project root."""
    embeddings = OpenAIEmbeddings()
    
    # Always save relative to project root (2 levels up from this file)
    root_path = Path(__file__).parent.parent.parent / save_path
    
    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(str(root_path))

    print(f"Index saved to {root_path}")
