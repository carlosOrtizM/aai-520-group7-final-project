import os
import sys
from dotenv import load_dotenv
from langchain_unstructured import UnstructuredLoader
from langchain_community.vectorstores.utils import filter_complex_metadata

# "Batch" preprocessing of a large number of documents. They are hypothetically coming in as .pdfs
# we want to turn them into Unstructured documents and feed them to Langchain objects.

# Rather than run this code in a main.py, I'll (hopefully) execute as a script, and maybe set up a
# recurring job, where we keep a list of documents in the system and last updated.
# If there is a new document or an updated document, we go delete the outdated copy and compute the new one.
# The tricky part is going to be keeping the vectorDB in sync.
# Maybe if we are using elasticsearch this can be managed internally (to a certain extent).

# We need two things to happen, document conversion and document partition.
# What we are aiming for is having a folder with all of the documents and we go to that folder and perform
# the preprocessing. First we'll use an OS folder and load the files into the program (in-memory).
# Later aiming to transition to a locally hosted elasticsearch DB/server.

load_dotenv()

root_path = os.getenv("ROOT_PATH", os.path.dirname(os.path.abspath(sys.argv[0])))
kb_path = os.path.join(os.getenv("PERSISTENCE_PATH"), os.getenv("KB_PATH"))

# Step 1 - Fetching from the OS - File System.
def directory_iterator():
    """This function fetches all pdfs found on the designated KB directory, sends them to be processed
    into langchain docs, and saves the langchain documents into a list.
    """
    docs = []
    try:
        for root, dirs, files in os.walk(os.path.join(root_path, kb_path), topdown=True):

            for direc in dirs:
                directory = os.path.join(os.fsdecode(root), os.fsdecode(direc))

            for name in files:
                filename = os.fsdecode(name)
                print(f"Processing {filename}, on {directory}.")

                if filename.endswith(".pdf"):
                    docs.append(langchain_docs_to_txt(os.path.join(directory, filename)))
                else:
                    print(f"Cannot process {filename}, on {directory} maybe it is not a PDF file.")

    except Exception as e:
        print(f"Error {e} on the initial preprocessing of files from {root_path}.")

    return docs

# Step 2 - Document conversion.
# Unstructured <- Images (Tesseract - OCR) <- pdf-to-image (Poppler)

# At first, we are only taking pdfs in. Word documents could be taken up later using LibreOffice
# and some other miscellaneous file types (e.g. .epub) by using pandoc.

# If parsing xml / html documents:
# brew install libxml2 libxslt

def tuple_edit(dict, key):
    dict[key] = ""

# using the langchain loader directly, as it uses unstructured under the hood anyway...
def langchain_docs_to_txt(complete_file_path):
    """This function converts the .pdf document into a langchain document."""
    try:
        filename = os.path.basename(complete_file_path).split('/')[-1]

        loader = UnstructuredLoader(complete_file_path,
            chunking_strategy="basic",
            max_characters=1000,
            overlap=220,
            unique_element_ids=False
        )
        docs = loader.load()

        # lengthy and not useful metadata field
        [tuple_edit(doc.metadata, key) for doc in docs for key, value in doc.metadata.items() if key == "orig_elements"]

        print(f"Sample document chunk: {docs[0]}\n\n")

        # we are loading and chunking, we could've also used a text splitter
        # e.g. RecursiveCharacterTextSplitter()

        # might need to filter metadata for now
        return filter_complex_metadata(docs)

    except Exception as e:
        print(f"Error {e} when turning the document {filename} to a langchain doc.")