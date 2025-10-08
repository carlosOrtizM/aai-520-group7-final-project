import utilities as util
import data_loader as data
import embedding_generator as embeddings
import model_initializer as model
import agent_creator as graph

import nltk
import ssl
import chromadb
import os
import gradio as gr

# pre-processing
DIR = os.path.dirname(os.path.abspath(__file__))

# utilities.clean_slate()
util.create_config()

data.folder_iterator()

# https://stackoverflow.com/questions/38916452/nltk-download-ssl-certificate-verify-failed
# dependecy errors...
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# nltk.download()... not needed
chunks = embeddings.document_splitter(embeddings.document_loader(embeddings.file_path_fetcher()))

# locally handle document addition
chroma_client = chromadb.HttpClient(host='localhost', port=8000, ssl=False)

vector_store = embeddings.vector_db_init(chunks, chroma_client)
print("Embeddings generated in initialized ChromaDB.\n")

model = model.llm_generator()
print("Llm initialized.\n")

graph = graph.graph_builder(vector_store, model)
print("Agentic Graph initialized.\n")

from IPython.display import Image


# uses api renderer
# Image(graph.get_graph().draw_mermaid_png(output_file_path = (DIR + "/graph.png")))

# Stateless, one-time chain

# input_message = "how can we leverage AI without losing our cognitive faculties (i.e. involution)?"

def output_print(prompt, history):
    response = ""

    for step in graph.stream(
            {"messages": [{"role": "user", "content": prompt}]},
            stream_mode="values",
    ):
        step["messages"][-1].pretty_print()
        response = step["messages"][-1]

    return str(response)


demo = gr.ChatInterface(
    fn=output_print,
    type='messages',
    theme="ocean",
    chatbot=gr.Chatbot(height=550),
    textbox=gr.Textbox(placeholder="AMA", container=False, scale=7)
)

demo.launch()