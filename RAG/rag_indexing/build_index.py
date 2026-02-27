import json
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

from rag_indexing.chunking import json_to_documents, split_documents
from rag_indexing.vectordb_client import build_vectorstore


# Load environment variables from .env
load_dotenv()


OUTPUT_DIR = Path("data/output")


def load_json_files(files: Optional[List[Path]] = None):
    docs = []
    json_files = files if files is not None else list(OUTPUT_DIR.glob("*.json"))

    for file in json_files:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        docs.extend(json_to_documents(data, source=str(file.name)))

    return docs


def build_index_for_files(files: Optional[List[Path]] = None):
    print("Loading extracted JSON files...")
    docs = load_json_files(files)

    print("Splitting into chunks...")
    splits = split_documents(docs)

    print("Building vector index...")
    build_vectorstore(splits)


def main():
    build_index_for_files()


if __name__ == "__main__":
    main()
