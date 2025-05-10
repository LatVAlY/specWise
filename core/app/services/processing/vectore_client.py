import json
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from qdrant_client import QdrantClient
# from qdrant_client.http.models import Distance, VectorParams
from langchain_openai import OpenAIEmbeddings
from dataclasses import dataclass, field
from uuid import uuid4

from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

openai_client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=api_key
)

embeddings = OpenAIEmbeddings(client=openai_client,
                              model="text-embedding-3-large")


@dataclass
class VectoreDatabaseClient:
    """
        everything about the vectore database client,
        create, update, delete and search
    """
    url: str
    client: QdrantClient = field(init=False)

    def __post_init__(self):
        self.client = QdrantClient(
            url=self.url
        )

    def transfer_str_to_documents(self, docs: list[str]) -> list[Document]:
        """ convert a list of strings to a list of documents """
        return [Document(page_content=doc, metadata={}) for doc in docs]

    def create_collection(self, docs: list[str]) -> str:
        """ create a vector collection for the client """
        try:
            documents = self.transfer_str_to_documents(docs)
            uid = str(uuid4())
            _ = QdrantVectorStore.from_documents(
                            documents,
                            embeddings,
                            url=self.url,
                            collection_name=uid
                        )
            return uid
        except Exception as e:
            print(f"Error creating collection: {e}")
            raise e

    def query_collection(self, collection_name: str, query: str) -> str:
        """ query a vector collection for the client """
        try:
            qdrant = QdrantVectorStore(
                url=self.url,
                collection_name=collection_name
            )
            docs = qdrant.similarity_search(query)
            return json.dumps(docs, default=lambda x: x.__dict__, indent=4)
        except Exception as e:
            print(f"Error querying collection: {e}")
            raise e


if __name__ == "__main__":
    vectore = VectoreDatabaseClient(url="localhost:6333")
    collection_name = vectore.create_collection(
        ["hello world", "hello world 2"])
    print(vectore.query_collection(collection_name, "hello world"))
