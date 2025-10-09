import os

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

import sys
from pathlib import Path

sys.path.append(str(Path(sys.prefix).parent / 'Dist_Packages'))

from dotenv import load_dotenv
load_dotenv()

root_path = os.getenv("ROOT_PATH", os.path.dirname(os.path.abspath(sys.argv[0])))
kb_path = os.getenv("KB_PATH")
partitioned_path = os.getenv("PARTITIONED_PATH", "Partitioned_KB")

# Step 1 - Fetching from the OS.
def directory_iterator():
    try:
        for root, dirs, files in os.walk(os.path.join(root_path, kb_path), topdown=True):

            for dir in dirs:
                directory = os.path.join(os.fsdecode(root), os.fsdecode(dir))

            for name in files:
                filename = os.fsdecode(name)
                print(f"Processing {filename}, on {directory}.")

                if filename.endswith(".pdf"):
                    pdf_to_txt(os.path.join(directory, filename))
                else:
                    print(f"Cannot process {filename}, on {directory} maybe it is not a PDF file.")

    except Exception as e:
        print(f"Error {e} when preprocessing files from {root_path}.")

# At first, we are only taking pdfs in. Word documents could be taken up later using LibreOffice
# and some other miscellaneous file types (e.g. .epub) by using pandoc.

# Step 2 - Document conversion.
# Unstructured <- Images (Tesseract - OCR) <- pdf-to-image (Poppler)

from unstructured.partition.pdf import partition_pdf
from unstructured.staging.base import elements_to_json
from unstructured.cleaners.core import replace_unicode_quotes

def pdf_to_txt(complete_file_path):
    filename =os.path.basename(complete_file_path).split('/')[-1]

    try:
        # partitioning is breaking down the whole document into elements, maybe there should be
        # a different partitioning approach? e.g. page-by-page, by title...
        elements = partition_pdf(complete_file_path)
        # additional cleaner functions exist, for now just removing special characters.
        for element in elements:
            replace_unicode_quotes(element.text)
        elements_to_json(elements=elements, filename=f"{os.path.join(root_path, partitioned_path)}/{filename}-output.json")

        print(f"Elements to JSON: {len(elements)}")

        # for pdfs with tables, we could use
        # elements = partition_pdf("complete_file_path", strategy="hi_res")

        # file-by-file preprocessing atm, we could eventually move to batch preprocessing
        # https://docs.unstructured.io/open-source/ingestion/overview

    except Exception as e:
        print(f"Error {e} when turning pdf to Unstructured elements (JSON) from {filename}.")

directory_iterator()