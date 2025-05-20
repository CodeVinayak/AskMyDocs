import os
from elasticsearch import Elasticsearch
from typing import List

ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "localhost")
ELASTICSEARCH_PORT = int(os.getenv("ELASTICSEARCH_PORT", 9200))
ELASTICSEARCH_URL = f"http://{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}"

# Add authentication if needed (e.g., when xpack.security.enabled is true)
# ELASTICSEARCH_USERNAME = os.getenv("ELASTICSEARCH_USERNAME")
# ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")

# es_client = Elasticsearch(
#     ELASTICSEARCH_URL,
#     basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD) if ELASTICSEARCH_USERNAME else None
# )

es_client = Elasticsearch(ELASTICSEARCH_URL)

INDEX_NAME = "document_chunks"

def create_index_if_not_exists():
    if not es_client.indices.exists(index=INDEX_NAME):
        es_client.indices.create(index=INDEX_NAME, ignore=400) # Ignore 400 if index already exists
        print(f"Elasticsearch index '{INDEX_NAME}' created.")
    else:
        print(f"Elasticsearch index '{INDEX_NAME}' already exists.")

def index_document_chunks(document_id: int, chunks: List[dict]):
    actions = [
        {
            "_index": INDEX_NAME,
            "_source": {
                "document_id": document_id,
                "chunk_text": chunk["chunk_text"],
                "metadata": chunk["metadata"] # Includes filename, s3_key, page, etc.
            }
        }
        for chunk in chunks
    ]
    # Use the bulk helper for efficient indexing
    from elasticsearch.helpers import bulk
    try:
        success_count, errors = bulk(es_client, actions)
        print(f"Indexed {success_count} document chunks for document ID {document_id}.")
        if errors:
            print(f"Errors during indexing: {errors}")
    except Exception as e:
        print(f"Error during bulk indexing: {e}") 