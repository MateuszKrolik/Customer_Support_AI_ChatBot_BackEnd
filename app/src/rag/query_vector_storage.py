# src/rag/query_vector_storage.py

import os, sys
from dataclasses import dataclass
from typing import List, Tuple, Optional
from langchain.schema import Document
from argparse import ArgumentParser
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from vector_storage_singleton import VectorStorageSingleton

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

BEDROCK_MODEL_ID = "anthropic.claude-instant-v1"
VECTOR_DB_PATH = "../data/chroma"


@dataclass
class QueryResponse:
    query_text: str
    response_text: str
    sources: List[Optional[str]]


def search_for_similarity(
        query_text: str,
) -> Optional[List[Tuple[Document, float]]]:  # float is the relevance score

    vector_storage_singleton = VectorStorageSingleton.instance()
    vector_storage = vector_storage_singleton.get_vector_storage

    # search db for top 3 best matches for query_text
    results = vector_storage.similarity_search_with_relevance_scores(query_text, k=3)

    # no results or first query is below given relevance score threshold
    if not results or results[0][1] < 0.1:  # 0-1 range, the bigger the stricter
        print("Couldn't find relevant data")
        return None
    return results


def query_rag(query_text: str) -> Optional[QueryResponse]:
    results = search_for_similarity(query_text)
    if not results:
        return None

    pages = []
    for doc, _score in results:
        pages.append(doc.page_content.strip())

    context_text = "\n\n---\n\n".join(pages)
    print(context_text)

    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)

    llm = ChatBedrock(model_id=BEDROCK_MODEL_ID)
    response = llm.invoke(prompt)
    response_content = response.content

    sources = []
    for doc, _score in results:
        # print(doc.metadata)
        # doc.metadata={"id": "source:page:chunk_index", "source": "path/to/data/file.pdf", "page": int}
        sources.append(doc.metadata.get("id", None))

    response_with_citations = f"Response: {response_content}\n\nSource: {sources}"
    print(response_with_citations)

    return QueryResponse(query_text=query_text, response_text=response_content, sources=sources)


def main() -> None:
    # cli parser
    parser = ArgumentParser()
    parser.add_argument("query_text", type=str, help="text to query vector store")
    args = parser.parse_args()
    query_text = args.query_text

    query_rag(query_text)


if __name__ == "__main__":
    main()
