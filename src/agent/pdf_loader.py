"""PDF -> langchain Document conversion.

Ported from g(old)/session_init/pdf_loader.py. Walks the configured
KB directory, loads each PDF with UnstructuredLoader, and returns
chunked langchain documents ready for embedding.
"""

import os

from src.config import KB_DIRECTORY


def directory_iterator(kb_directory: str | None = None) -> list:
    """Walk the KB directory and convert every PDF found into chunks."""
    target = kb_directory or str(KB_DIRECTORY)
    docs = []
    if not os.path.isdir(target):
        return docs

    for root, _dirs, files in os.walk(target, topdown=True):
        for name in files:
            if not name.lower().endswith(".pdf"):
                continue
            chunks = _pdf_to_langchain_docs(os.path.join(root, name))
            if chunks:
                docs.append(chunks)
    return docs


def _pdf_to_langchain_docs(path: str):
    from langchain_community.vectorstores.utils import filter_complex_metadata
    from langchain_unstructured import UnstructuredLoader

    loader = UnstructuredLoader(
        path,
        chunking_strategy="basic",
        max_characters=1000,
        overlap=220,
        unique_element_ids=False,
    )
    docs = loader.load()
    for doc in docs:
        if "orig_elements" in doc.metadata:
            doc.metadata["orig_elements"] = ""
    return filter_complex_metadata(docs)
