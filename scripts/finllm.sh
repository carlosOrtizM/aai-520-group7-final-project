#!/usr/bin/env python

#Going up one directory, as .sh files are currently under the scripts folder
function pfinder {

  SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
  cd "$SCRIPT_DIR" || echo "Error going into $SCRIPT_DIR"
  cd .. || echo "Error going one level up the $SCRIPT_DIR"
  SCRIPT_DIR=$( pwd )
  echo $SCRIPT_DIR

}

RESPONSE=$(pfinder)
cd "$RESPONSE" || echo "Error going into $RESPONSE"

# cd llama.cpp || echo "Error going into llama.cpp."
# pip install -r requirements.txt | grep -v 'already satisfied'

hf download andrijdavid/finance-chat-GGUF finance-chat-Q2_K.gguf --local-dir gguf_models

echo "Please go ahead and manually configure the Modelfile under /gguf_models in case you are using a different model."

#python convert_hf_to_gguf.py ../outputs_custom_llm/ --outfile ../gguf_models/fingpt-mt_llama2-7b_lora.gguf