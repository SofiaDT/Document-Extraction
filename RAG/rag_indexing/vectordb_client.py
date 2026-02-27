from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


def build_vectorstore(documents, save_path="faiss_index"):
    embeddings = OpenAIEmbeddings()

    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(save_path)

    print(f"Index saved to {save_path}")
