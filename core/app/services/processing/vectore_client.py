import json
from langchain_qdrant import Qdrant
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_openai import OpenAIEmbeddings
from dataclasses import dataclass
from uuid import uuid4
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

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
            base_url="https://openrouter.ai/api/v1", api_key=openai_api_key
        )
        self.embeddings = OpenAIEmbeddings(
            api_key=openai_api_key,
            model="text-embedding-3-large")

    def transfer_str_to_documents(self, docs: list[str]) -> list[Document]:
        """convert a list of strings to a list of documents"""
        return [Document(page_content=doc, metadata={}) for doc in docs]

    def create_collection(self, collection_id: str, items: list[str]):
        """create a vector collection for the client"""
        try:
            docs = self.transfer_str_to_documents(items)
            # create a collection with the uid

            self.client.recreate_collection(
                collection_name=collection_id,
                vectors_config=VectorParams(
                    size=3072,
                    distance=Distance.COSINE,
                ),
            )
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
    def add_documents(self, collection_id: str, items: list[str]):
        """add documents to a vector collection for the client"""
        try:
            docs = self.transfer_str_to_documents(items)
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
            print(f"Error adding documents: {e}")
            raise e
    def query_collection(self, collection_name: str, query: str, k=5) -> str:
        """query a vector collection for the client"""
        try:
            qdrant = Qdrant(
                client=self.client,
                collection_name=collection_name,
                embeddings=self.embeddings,
            )
            docs = qdrant.similarity_search(query, k=k)
            return docs
        except Exception as e:
            print(f"Error querying collection: {e}")
            raise e

    def store_data(self, user_id, collection_id: str, data):
        """ store data in a vector collection for the client """
        try:
            docs = [str(filter(lambda attr, _: attr != "classification_item",
                               vars(item).items())) for item in data]
            print(docs)
            documents = self.transfer_str_to_documents(docs)
            _ = Qdrant.from_documents(
                            documents,
                            embedding=self.embeddings,
                            url=self.url,
                            collection_name=collection_id)
        except Exception as e:
            print(f"Error storing data: {e}")
            raise e


if __name__ == "__main__":
    vectore = VectoreDatabaseClient()
    collection_id = "15135346-2baa-45fc-9786-b66ee81b0b2f"
    collection_name = vectore.create_collection(
        collection_id=collection_id, items=["hello world", "hello world 2"]
    )
    # print(f"Collection name: {collection_name}")
    print(vectore.query_collection(collection_name=collection_id, query="hello"))
