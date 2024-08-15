import os
from typing import List, Tuple, Optional
from langchain.schema import Document
from argparse import ArgumentParser
from langchain_aws import BedrockEmbeddings
from langchain_chroma import Chroma

DB_PATH = os.path.join(os.path.dirname(__file__), "chroma")


def search_for_similarity(
    query_text: str,
) -> Optional[List[Tuple[Document, float]]]:  # float is the relevance score
    vector_store = Chroma(
        embedding_function=BedrockEmbeddings(), persist_directory=DB_PATH
    )

    # search db for top 3 best matches for query_text
    results = vector_store.similarity_search_with_relevance_scores(query_text, k=3)

    # empty results or first query is below given relevance score threshold
    if not results or results[0][1] < 0.5:  # 0-1 range, the bigger the stricter
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

    result = []
    for doc, _score in results:
        result.append(doc.page_content.strip())

    context_text = "\n\n---\n\n".join(result)
    print(context_text)


if __name__ == "__main__":
    main()
