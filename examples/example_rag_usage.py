"""Quick examples of RAG store usage for searching and processing documents."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "Document_Extraction"))
from src.rag_store import create_rag_store


def main():
    """Quick examples of RAG usage patterns."""
    
    # Initialize the RAG store
    rag_store = create_rag_store({
        "persist_directory": "data/vectorstore",
        "chunk_size": 1000,
        "chunk_overlap": 200
    })
    
    stats = rag_store.get_stats()
    print(f"RAG Store: {stats}\n")
    
    # Example 1: Simple semantic search
    print("1. Semantic Search")
    results = rag_store.search("receipts with payment information", k=3)
    for i, doc in enumerate(results, 1):
        print(f"  {i}. {doc.metadata.get('file_name')} ({doc.metadata.get('document_type')})")
    
    # Example 2: Search with relevance scores
    print("\n2. Search with Scores")
    results = rag_store.search_with_scores("merchant transactions", k=3)
    for i, (doc, score) in enumerate(results, 1):
        print(f"  {i}. {doc.metadata.get('file_name')} - Score: {score:.3f}")
    
    # Example 3: Filtered search by document type
    print("\n3. Filter by Document Type")
    receipts = rag_store.search(
        "payment information",
        k=5,
        filter_metadata={"document_type": "receipt"}
    )
    for receipt in receipts:
        if receipt.metadata.get("chunk_index") == 0:
            merchant = receipt.metadata.get('field_merchant_name', 'N/A')
            total = receipt.metadata.get('field_total_amount', 'N/A')
            print(f"  {merchant}: ${total}")
    
    # Example 4: Question-answering style queries
    print("\n4. Natural Language Queries")
    questions = [
        "What receipts are from Walmart?",
        "Show me bank statements",
        "Which documents have high confidence?",
    ]
    for question in questions:
        results = rag_store.search(question, k=1)
        print(f"  Q: {question}")
        if results:
            print(f"     → {results[0].metadata.get('file_name')}")


if __name__ == "__main__":
    # Check if vectorstore exists
    vectorstore_path = Path("data/vectorstore")
    if not vectorstore_path.exists() or not (vectorstore_path / "index.faiss").exists():
        print("✗ No vectorstore found!")
        print("\nCreate one with:")
        print("  python -m rag_indexing.build_index")
    else:
        try:
            main()
        except Exception as e:
            print(f"Error: {e}")
            print("\nMake sure you have:")
            print("1. Dependencies installed: pip install -r requirements.txt")
            print("2. OPENAI_API_KEY set in .env or environment")
            print("3. Indexed documents: python -m rag_indexing.build_index")
