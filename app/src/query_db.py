import os
from typing import List, Tuple, Optional
from langchain.schema import Document
from argparse import ArgumentParser
from langchain_aws import ChatBedrock
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from get_embedding_func import get_embedding_func

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

BEDROCK_MODEL_ID = "anthropic.claude-instant-v1"

DB_PATH = os.path.join(os.path.dirname(__file__), "chroma")


def search_for_similarity(
        query_text: str,
) -> Optional[List[Tuple[Document, float]]]:  # float is the relevance score
    vector_store = Chroma(
        embedding_function=get_embedding_func(), persist_directory=DB_PATH
    )

    # search db for top 3 best matches for query_text
    results = vector_store.similarity_search_with_relevance_scores(query_text, k=3)

    # no results or first query is below given relevance score threshold
    if not results or results[0][1] < 0.1:  # 0-1 range, the bigger the stricter
        print("Couldn't find relevant data")
        return
    return results


def main() -> None:
    # cli parser
    parser = ArgumentParser()
    parser.add_argument("query_text", type=str, help="text to query vector store")
    args = parser.parse_args()
    query_text = args.query_text

    results = search_for_similarity(query_text)
    if not results:
        return

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


if __name__ == "__main__":
    main()
