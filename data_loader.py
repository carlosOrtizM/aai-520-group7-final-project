# Fetch all files from the corresponding folder. Since they are pdfs, turn them into .txts

# Took some books from https://www.openhumanitiespress.org/
# and some of the writings on https://digital.library.illinois.edu/collections/38ec6eb0-18c3-0135-242c-0050569601ca-1
# Remove special characters in the process

# https://www.geeksforgeeks.org/python/convert-pdf-to-txt-file-using-python/

import pdfplumber
import os
from configparser import ConfigParser


# https://configu.com/blog/working-with-python-configuration-files-tutorial-best-practices/

def path_fetcher(**kwargs):
    # Create a ConfigParser object
    config_object = ConfigParser()

    # Read the configuration from the 'config.ini' file
    config_object.read("config.ini")

    # Access the Path section
    path = config_object["Path"]

    option = kwargs.get('option', None)

    if option == 1:
        return path["pdfs"]
    elif option == 2:
        return path["txts"]

    return path["root"]


# could've used the unstructured library for pdfs directly...
def pdf_to_txt(complete_path, filename):
    write_path = os.path.join(path_fetcher() + path_fetcher(option=2), os.path.splitext(filename)[0])
    symbols = ['?', '%', '&', '$', '(', ')', '!', '-', '+', '=', " ", ",", "'", '"', "/", ".", ";"
        , "\\", "\'", "\"", "\a", "\b", "\f", "\n", "\r", "\t", "\v"
        , " \\", " \'", " \"", " \a", " \b", " \f", " \n", " \r", " \t", " \v"]

    with pdfplumber.open(complete_path) as pdf:

        page_index = 0

        for page in pdf.pages:
            with open(os.path.join(write_path + str(page_index) + ".txt"), "w", encoding="utf-8") as f:
                t = page.extract_text()
                if t:
                    new_t = ""
                    for char in t:
                        if char.isalnum() or char in symbols:
                            new_t = new_t + char

                    page_index = page_index + 1

                    if len(new_t) > 5400 or len(new_t) < 1:
                        print("Skipped page, was too lengthy or null.")
                    else:
                        f.write(new_t + '\n')


# https://stackoverflow.com/questions/10377998/how-can-i-iterate-over-files-in-a-given-directory
def folder_iterator():
    directory = os.fsencode(path_fetcher() + path_fetcher(option=1))

    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".pdf"):
            pdf_to_txt(os.path.join(os.fsdecode(directory), filename), filename)
            print(f"Imported {filename}\n")
            continue
        else:
            continue