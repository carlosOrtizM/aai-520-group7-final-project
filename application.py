import sys
import dotenv
from utilities.core_utils import get_y_n, render_graph, authenticate_user
from session_init.pdf_loader import directory_iterator
from session_init.chroma_generator import vector_db_initializer
from session_init.llm_loader import llm_client_loader
from session_init.rag_builder import graph_builder
from session_init.gradio_loader import gradio_ui_loader
from pathlib import Path
import shutil
import os

def main():
    try:
        sys.path.append(str(Path(sys.prefix).parent / 'third_p_modules'))
        dotenv.load_dotenv()

        # One-time Initialization: ("Batch") document pre-processing, vectorDB setup, Langgraph compiling.
        print(f"Do you want to load any documents? [Y/N].")
        response = "True" if get_y_n() == "Y" else "False"

        if response == "True":
            print(f"Initializing...")
            try:
                # from pdfs to Langchain docs
                docs = directory_iterator()

                # insert the Langchain docs (as embeddings) to the ChromaDB
                vector_store = vector_db_initializer(docs)

            except Exception as e:
                print(f"Error {e} during the One-time Initialization process.")

        # Mandatory start-up: get our Ollama and chroma clients up and running.
        # Also (not yet) make sure their corresponding servers are up and running.
        # Also (not yet) make sure they are updated, document-and-model-wise.
        try:
            # Initializing from scratch always for now
            llm_client = llm_client_loader()

            # Now it's just one graph, in the future there will be more...
            rag_graph = graph_builder(vector_store, llm_client)
            render_graph(rag_graph) if response=='True' else None

            gradio_ui_loader(rag_graph).launch(auth=authenticate_user)

        except Exception as e:
            print(f"Error {e} loading clients, graphs, and the GradioUI")

    except KeyboardInterrupt:
        print("KeyboardInterrupt detected. Cleaning up and exiting...")
        sys.exit(0)  # Exit gracefully with exit status 0

    finally:
        path = os.path.join(os.getenv("ROOT_PATH"), os.getenv("PERSISTENCE_PATH"), os.getenv("VECTOR_DB_PATH"))
        shutil.rmtree(path)
        os.mkdir(path)


if __name__ == "__main__":
    main()