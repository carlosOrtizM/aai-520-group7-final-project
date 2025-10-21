import os
from uuid import uuid4

import dotenv

def init_folder(path):
    dotenv.load_dotenv()
    return os.getenv("INITIALIZE")

#CLI prompting for Y/N
def get_y_n():

    while True:
        prompt = input()

        try:
            value = str(prompt)
        except ValueError:
            print("Sorry, I didn't understand that.")
            continue

        if value == "Y" or value == "N":
            return value
        else:
            print("Sorry, your response must not be either Y or N.")
            continue

from langchain_core.runnables.graph import MermaidDrawMethod
from IPython.display import Image

# Render graph visualizations
def render_graph(graph_instance):

    dotenv.load_dotenv()
    path = os.path.join(os.getenv("ROOT_PATH"), os.getenv("PERSISTENCE_PATH"),os.getenv("APP_OUT_PATH")) + f"/{str(uuid4())}" + ".png"
    graph = Image(graph_instance.get_graph().draw_mermaid_png(output_file_path=(path)))

def authenticate_user(username, password):
    """
    Simple authentication for restricted access
    """
    dotenv.load_dotenv()
    valid_users = {
        os.getenv("GRADIO_USERNAME", "admin"): os.getenv("GRADIO_PASSWORD", "password")
    }

    return valid_users.get(username) == password