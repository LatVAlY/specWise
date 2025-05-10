import json
from langchain_qdrant import Qdrant
from langchain_core.documents import Document
from qdrant_client import QdrantClient

from qdrant_client.http.models import Distance, VectorParams
from langchain_openai import OpenAIEmbeddings

from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")


class VectoreDatabaseClient:
    """
    everything about the vectore database client,
    create, update, delete and search
    """

    def __init__(self):
        self.url = "localhost:6333"
        self.client = QdrantClient(url=self.url)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.openai_client = OpenAI(
            base_url="https://openrouter.ai/api/v1", api_key=api_key
        )

    def transfer_str_to_documents(self, docs: list[str]) -> list[Document]:
        """convert a list of strings to a list of documents"""
        return [Document(page_content=doc, metadata={}) for doc in docs]

    def create_collection(self, collection_id: str, items: list[str]):
        """create a vector collection for the client"""
        try:
            docs = self.transfer_str_to_documents(items)
            # create a collection with the uid
            exist = self.client.collection_exists(collection_id)
            if not exist:
                self.client.recreate_collection(
                    collection_name=collection_id,
                    vectors_config=VectorParams(
                        size=3072,
                        distance=Distance.COSINE,
                    ),
                )
                print(f"Collection {docs} created")
            vector_store = Qdrant.from_documents(
                docs,
                self.embeddings,
                url=self.url,
                prefer_grpc=False,
                collection_name=collection_id,
                force_recreate=False,
            )
            vector_store.add_documents(docs)

        except Exception as e:
            print(f"Error creating collection: {e}")
            raise e

    def query_collection(self, collection_name: str, query: str) -> str:
        """query a vector collection for the client"""
        try:
            qdrant = Qdrant(
                client=self.client,
                collection_name=collection_name,
                embedding=self.embeddings,
            )
            docs = qdrant.similarity_search(query)
            return docs
        except Exception as e:
            print(f"Error querying collection: {e}")
            raise e


if __name__ == "__main__":
    vectore = VectoreDatabaseClient()
    collection_id = "15135346-2baa-45fc-9786-b66ee81b0b2f"
    collection_name = vectore.create_collection(
        collection_id=collection_id, items=["hello world", "hello world 2"]
    )
    # print(f"Collection name: {collection_name}")
    print(vectore.query_collection(collection_name=collection_id, query="hello"))
