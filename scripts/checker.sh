#!/bin/bash

# Check for Python and Ollama, or else throw warning them.

vchecker() {

  command="! command -v $1"

  if  eval "$command" ;then
    # Download this specific application
    echo "Dont forget to download $1"
  else
    echo "$1 found in system."
  fi

}

vchecker python
vchecker ollama

ollamacheck(){

  command=" command -v ollama"

  if eval "$command" ;then
    command=" command ollama run fingpt-mt_llama2-7b_lora"

    if eval "$command" ;then
      echo "FinLLM model running."
    else
      echo "Do you want me to install the fin-llm from the Internet? (Y/n)"
      read char

      if [ "$char" = "Y" ];then
        SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
        cd "$SCRIPT_DIR" || echo "Error going into $SCRIPT_DIR"
        #cd .. || echo "Error going one level up the $SCRIPT_DIR"
        #echo "Do you want me to install llama.cpp from the Internet? (Y/n)"
        #read char

        #if [ "$char" = "Y" ];then
        #  git clone https://github.com/ggerganov/llama.cpp.git
        #fi

        source finllm.sh || echo "Error running finllm.sh"

      else
        SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
        cd "$SCRIPT_DIR" || echo "Error going into $SCRIPT_DIR"
        cd ../ggufmodels || echo "Error going into /ggufmodels."
        ollama create finance-chat-Q2_K.gguf -f Modelfile || echo "Missing the model, please go download and configure in ollama,
        or change to your LlM of choice. Found at: https://huggingface.co/FinGPT/fingpt-mt_llama2-7b_lora"
      fi

    fi

  fi

}

ollamacheck || echo "Error searching for the finllm."