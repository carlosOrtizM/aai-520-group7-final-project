#!/bin/bash

#Script to create or just activate python virtual environments...

#Going up one directory, as .sh files are currently under the scripts folder
function pfinder {

  SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
  cd "$SCRIPT_DIR" || echo "Error going into $SCRIPT_DIR"
  cd .. || echo "Error going one level up the $SCRIPT_DIR"
  SCRIPT_DIR=$( pwd )
  echo $SCRIPT_DIR

}

STRING="Loading the python virtual environment (MacOS/Linux)."
echo $STRING

SCRIPT_DIR=$(pfinder)

function venv {

  VENV_DIR="$SCRIPT_DIR/.venv"
  # Create the virtual environment if it does not exist
  if [ -d $VENV_DIR ]; then
    echo 0

  else

      if [ ! command -v python ];then
        python -m venv .venv
        echo 0

      else
        echo 1

      fi

  fi
}

RESPONSE=$(venv)

if [ "$RESPONSE" -eq 0 ]; then
  # Activate the virtual environment if it exists
  source "$SCRIPT_DIR/.venv/bin/activate"
  echo "Virtual environment activated."

else
  echo "Something went wrong, maybe (source) Python is missing?"
  echo "Try creating the virtual environment yourself, sorry... useful guide at https://python.land/virtual-environments/virtualenv"
fi

