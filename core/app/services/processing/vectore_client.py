import json
from langchain_qdrant import QdrantVectorStore, RetrievalMode
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_openai import OpenAIEmbeddings
from dataclasses import dataclass
from uuid import uuid4
from openai import OpenAI
from dotenv import load_dotenv
import os

from core.app.models.models import ItemDto

url = "http://localhost:6333"  # Qdrant URL


# Load environment variables from .env file
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

openai_client = OpenAI(api_key=openai_api_key)


@dataclass
class VectoreDatabaseClient:
    """
        everything about the vectore database client,
        create, update, delete and search
    """
    url: str

    def __post_init__(self):
        self.client = QdrantClient(
            url=self.url
        )
        self.embeddings = OpenAIEmbeddings(
            api_key=openai_api_key,
            model="text-embedding-3-large")

    def transfer_str_to_documents(self, docs: list[str]) -> list[Document]:
        """ convert a list of strings to a list of documents """
        return [Document(page_content=doc, metadata={}) for doc in docs]

    def create_collection(self, docs: list[str]) -> str:
        """ create a vector collection for the client """
        try:
            collection_id = str(uuid4())
            self.client.create_collection(
                collection_name=collection_id,
                vectors_config=VectorParams(size=4,
                                            distance=Distance.DOT))
            documents = self.transfer_str_to_documents(docs)
            _ = QdrantVectorStore.from_documents(
                            documents=documents,
                            embedding=self.embeddings,
                            retrieval_mode=RetrievalMode.DENSE,
                            url=self.url,
                            collection_name=collection_id
                        )
            return collection_id
        except Exception as e:
            print(f"Error creating collection: {e}")
            raise e

    def query_collection(self, collection_name: str, query: str) -> str:
        """ query a vector collection for the client """
        try:
            qdrant = QdrantVectorStore(
                client=self.client,
                collection_name=collection_name
            )
            docs = qdrant.similarity_search(query)
            return json.dumps(docs, default=lambda x: x.__dict__, indent=4)
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
            _ = QdrantVectorStore.from_documents(
                            documents,
                            embedding=self.embeddings,
                            url=self.url,
                            collection_name=collection_id)
        except Exception as e:
            print(f"Error storing data: {e}")
            raise e


if __name__ == "__main__":
    vectore = VectoreDatabaseClient(url="localhost:6333")
    collection_name = vectore.create_collection(
        ["hello world", "hello world 2"])
    print(vectore.query_collection(collection_name, "hello world"))
    vectore.store_data("user_id", collection_name, [
        ItemDto(ref_no="123", description="test", quantity=1, unit="kg")])
