import os
import shutil
from typing import List
from langchain_community.document_loaders.pdf import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_chroma import Chroma
from get_embedding_func import get_embedding_func

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(os.path.dirname(__file__), "chroma")


def load_documents():
    document_loader = PyPDFDirectoryLoader(DATA_PATH)
    return document_loader.load()


def split_text(documents: List[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=20,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    return chunks


def save_to_vector_storage(chunks: List[Document]):
    # recursively clear out the db first if present
    clear_db()
    # create vector store db
    vector_store = Chroma(
        # documents=chunks,
        persist_directory=DB_PATH,  # local vector storage
        embedding_function=get_embedding_func(),
        collection_metadata={
            "hnsw:space": "cosine"
        },  # for relevance scores to be between 0-1
    )

    chunks_with_ids = calculate_chunk_ids(chunks)

    # fetch IDs only w/o additional data (internal implementation)
    # https://cookbook.chromadb.dev/core/collections/#getting-ids-only
    # and turn them into a set for uniqueness and faster lookup
    existing_items = vector_store.get(include=[])
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing docs in db: {len(existing_ids)}")

    # filter through existing docs and add only new ones
    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)

    if new_chunks:
        print(f"adding {len(new_chunks)} new chunks to db...")
        new_chunk_ids = []
        for chunk in new_chunks:
            new_chunk_ids.append(chunk.metadata["id"])
        # kwargs prevents chroma from automatically setting the id's,
        # which would cause a problem when checking for existing id's in custom format
        vector_store.add_documents(new_chunks, ids=new_chunk_ids)
    else:
        print("no new chunks to add.")

    print(f"saved {len(chunks)} chunks into {DB_PATH}.")


def calculate_chunk_ids(chunks: List[Document]) -> List[Document]:
    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source", None)  # fallback none for keyError
        page = chunk.metadata.get("page", None)
        current_page_id = f"{source}:{page}"  # handle multiple sources
        if current_page_id == last_page_id:
            current_chunk_index += 1  # increment chunk counter if the page/source is the same
        else:
            current_chunk_index = 0  # reset chunk counter if the page changes

        chunk_id = f"{current_page_id}:{current_chunk_index}"
        # chunk_id = f"{source}:{page}:{chunk_index}"
        last_page_id = current_page_id

        # add chunk id's to page metadata
        chunk.metadata["id"] = chunk_id
        # chunk.metadata={"id": "source:page_id:chunk_id", "source": "path/to/data/file.pdf", "page": int}
    return chunks


def generate_vector_store_db():
    documents = load_documents()
    chunks = split_text(documents)
    save_to_vector_storage(chunks)


def clear_db() -> None:
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)


def main():
    generate_vector_store_db()


if __name__ == "__main__":
    main()
