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

#install the requirements as in the requirements.txt
pip install -r requirements.txt | grep -v 'already satisfied'

echo "Requirements up to date."

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