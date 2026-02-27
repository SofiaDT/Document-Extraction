from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document


def json_to_documents(data: dict, source: str):
    """
    Convert extracted JSON into LangChain Documents.
    Assumes your extraction output is structured JSON.
    Simplify: flatten everything into text.
    """
    text = str(data)

    return [
        Document(
            page_content=text,
            metadata={"source": source},
        )
    ]


def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    return splitter.split_documents(docs)
