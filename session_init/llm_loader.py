import os
from langchain_ollama import ChatOllama
from utilities.metric_utils import basic_logger
from dotenv import load_dotenv

# Initialize an Ollama Client for our generative Llm model

load_dotenv()
text_model = os.getenv("TEXT_MODEL")

@basic_logger
def llm_client_loader():
    """This function serves an Ollama-hosted text generator model, to be used by our graphs."""
    try:
        llm = ChatOllama(
            model=text_model,
            temperature=0.2
        )
        return llm
    except Exception as e:
        print(f"Error {e} instantiating the Ollama client, is the Ollama server running?.")

# could add something to verify Ollama is running