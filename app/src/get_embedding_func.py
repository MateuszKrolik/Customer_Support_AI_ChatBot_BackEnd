from langchain_aws import BedrockEmbeddings

def get_embedding_func()->BedrockEmbeddings:
    embeddings = BedrockEmbeddings()
    return embeddings