# Initialize VectorDB and create embeddings

# https://medium.com/@isurulkh/simple-rag-app-using-ollama-and-langchain-96ea10bf79ce
# https://www.datacamp.com/tutorial/llama-3-1-rag
# https://python.langchain.com/docs/tutorials/rag/

import os
from configparser import ConfigParser

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

# https://docs.trychroma.com/docs/overview/telemetry
from chromadb.config import Settings

from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader

from unstructured.partition.auto import partition
from unstructured.chunking.basic import chunk_elements

from langchain_community.vectorstores.utils import filter_complex_metadata

from langchain_text_splitters import RecursiveCharacterTextSplitter


def embedding_fetcher():
    # Create a ConfigParser object
    config_object = ConfigParser()

    # Read the configuration from the 'config.ini' file
    config_object.read("config.ini")

    # Access the Path section
    model = config_object["Embedding"]

    return model["name"]


def docs_fetcher():
    # Create a ConfigParser pip object
    config_object = ConfigParser()

    # Read the configuration from the 'config.ini' file
    config_object.read("config.ini")

    # Access the Path section
    path = config_object["Path"]

    return path["root"] + path["txts"]


def embedder():
    return OllamaEmbeddings(model=embedding_fetcher())


def file_path_fetcher():
    path = docs_fetcher()

    directory = os.fsencode(path)
    file_paths = []

    for file in os.listdir(directory):

        filename = os.fsdecode(file)

        if filename.endswith(".txt"):
            file_paths.append(os.path.join(path, filename))

    return file_paths


# need to batch it
def document_loader(file_paths):
    print(f"Loading .txt files.\n")

    for file_path in file_paths:
        loader = TextLoader(file_path)

        docs = loader.load()

    # needs to be lower than 5000
    print("LangChain documents created.\n")

    return filter_complex_metadata(docs)


def document_splitter(docs):
    # Initialize a text splitter with specified chunk size and overlap
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=550,
                                                   chunk_overlap=42,
                                                   # Specifies a function to calculate the length of the string.
                                                   length_function=len,
                                                   # Sets whether to use regular expressions as delimiters.
                                                   is_separator_regex=False
                                                   )

    # Split the documents into chunks
    doc_splits = text_splitter.split_documents(docs)
    print(f"Sample Document split print: {doc_splits[0].page_content}\n")

    return doc_splits


def vector_db_init(chunks, client):
    vector_store = Chroma(
        client=client,
        collection_name="systemic_collection",
        embedding_function=embedder(),
        persist_directory="./chroma",  # "./chroma_langchain_db" Where to save data locally, remove if not necessary
        client_settings=Settings(anonymized_telemetry=False)
    )

    # Index chunks
    _ = vector_store.add_documents(documents=chunks)

    return vector_store