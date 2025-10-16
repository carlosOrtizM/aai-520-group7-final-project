import os
import uuid

from chromadb.api.shared_system_client import SharedSystemClient
from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from langchain_chroma import Chroma # https://docs.trychroma.com/docs/overview/telemetry
from chromadb.config import Settings
from utilities.metric_utils import basic_logger

# Initialize VectorDB and create initial embeddings, we are using ChromaDB at the moment.
# But it might be better if we use elasticsearch instead (later).

load_dotenv()
embedding_model = os.getenv("EMBEDDING_MODEL")
chroma_directory = os.path.join(os.getenv("PERSISTENCE_PATH"), os.getenv("VECTOR_DB_PATH"))
chroma_collection = os.getenv("CHROMA_COLLECTION")

def embedder():
    """This function serves an Ollama-hosted embedding model, to encode and decode vectors in our vector store."""
    return OllamaEmbeddings(model=embedding_model)

@basic_logger
def vector_db_initializer(documents):
    """This function initializes the vector store, encoding the initial batch of langchain docs into vectors."""
    try:
        vector_store = Chroma(
            collection_name=chroma_collection,
            embedding_function=embedder(),
            persist_directory=chroma_directory,
            client_settings=Settings(anonymized_telemetry=False)
        )

        f_documents = []
        [f_documents.append(Document(
            page_content=chunk.page_content, metadata=chunk.metadata,id=chunk.metadata['page_number'],)
        ) for document in documents for chunk in document]

        ids = []
        [ids.append(str(uuid.uuid4())) for i in range(len(f_documents))]

        vector_store.add_documents(documents=f_documents, ids=ids)
        print(f"Inserted documents: {len(f_documents)}")

        return vector_store

    except Exception as e:
        print(f"Error {e} initializing the ChromaDB vector store with the langchain_documents[].")