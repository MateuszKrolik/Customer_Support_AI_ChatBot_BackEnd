import os
import shutil
from typing import List
from langchain_community.document_loaders.pdf import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_aws import BedrockEmbeddings
from langchain_chroma import Chroma

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(os.path.dirname(__file__), "chroma")


def load_documents():
    document_loader = PyPDFDirectoryLoader(DATA_PATH)
    return document_loader.load()


def split_text(documents: List[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=500, length_function=len, add_start_index=True
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    document = chunks[5]
    print(document.page_content)
    print(document.metadata)
    return chunks


def save_to_vector_storage(chunks: List[Document]):
    # recursively clear out the db first if present
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)
    # create vector store db
    Chroma.from_documents(
        chunks,
        BedrockEmbeddings(),
        persist_directory=DB_PATH,  # local vector storage
    )
    print(f"Saved {len(chunks)} chunks into {DB_PATH}.")


def generate_vector_store_db():
    documents = load_documents()
    chunks = split_text(documents)
    save_to_vector_storage(chunks)


def main():
    generate_vector_store_db()


if __name__ == "__main__":
    main()
