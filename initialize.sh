#!/bin/bash
# Execute the other initialization scripts

#Going to /scripts directory, as .sh files are currently under the scripts folder
function pfinder {

  SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
  cd "$SCRIPT_DIR" || echo "Error going into $SCRIPT_DIR"
  cd scripts || echo "Error going into /scripts from $SCRIPT_DIR"
  SCRIPT_DIR=$( pwd )
  echo $SCRIPT_DIR

}

SCRIPT_DIR=$(pfinder)

executor() {

  command="source $1/$2"
  eval "$command"

}

executor "$SCRIPT_DIR" venv.sh || echo "Error running venv.sh"
SCRIPT_DIR="$(pfinder)/scripts"
executor "$SCRIPT_DIR" reqs.sh || echo "Requirements already satisfied."
executor "$SCRIPT_DIR" checker.sh || echo "Error running checker.sh"

echo "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⣤⣀⠀⠀⠀"
echo "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣾⣿⣿⣿⣿⣷⠀⠀"
echo "⠀⠀⠀⠀⠀⠀⠀⣠⠴⠒⠋⢉⡝⠲⢦⡀⠀⠀⠀⠀⠀⠸⣿⣿⣿⣿⣿⣿⠀⠀"
echo "⠀⠀⠀⠀⢀⡴⠚⢡⣤⣤⣴⣾⣷⣷⣨⢷⣀⡀⠀⠀⠀⠀⠹⢿⣿⣿⡿⠋⠀⠀"
echo "⠀⢀⣠⠴⠋⠀⠀⠘⣟⡛⡽⡹⣫⣿⣴⣤⠿⣿⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"
echo "⠈⠉⠁⢰⡦⡄⠀⣤⠌⣷⣷⣷⢣⠟⠛⠻⣼⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠"
echo "⢰⣾⣶⣦⢿⣭⣆⡻⣿⣿⣿⣻⣸⡀⠀⠃⠿⠷⠂⠀⠀⠀⠀⠀⠀⠀⠀⢀⠔⠁"
echo "⢸⣿⢿⣿⣎⢿⢿⣿⡿⠛⠛⠳⣿⣧⡀⠰⣿⠂⠀⠀⠀⠀⠀⠀⠀⣠⠖⠁⢀⠾"
echo "⠀⠙⢿⣿⣿⣿⠟⠋⠀⠀⠀⠀⠀⠙⠿⣦⣄⣀⡀⠀⣀⣀⣠⠴⠚⣁⡠⣾⣯⢟"
echo "⠀⠠⣄⣀⣀⡀⠲⡄⠰⠒⠃⡴⣶⣦⡐⢄⣯⣍⡛⠛⠉⢉⡀⢀⣩⠵⠶⠛⡵⢛"
echo "⠀⣤⣾⠛⣟⣹⣦⣒⣢⢿⣾⣧⡸⢙⠿⣶⣷⣬⣊⣳⣿⣽⣟⡟⠛⣋⣒⣓⣒⣪"
echo "⠀⠿⠃⠀⠹⠿⠿⠧⠴⠶⠾⡿⠇⠤⠕⠚⠿⠿⠟⠻⠛⠭⠥⠶⠭⠭⠤⠤⠤⠤"