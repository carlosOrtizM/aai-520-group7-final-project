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