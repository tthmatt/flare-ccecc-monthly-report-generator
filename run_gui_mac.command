#!/bin/bash
set -e
python3 gui_app.py || {
  echo ""
  echo "If this failed because Python packages are missing, run:"
  echo "pip3 install -r requirements.txt"
}
echo ""
read -p "Press enter to exit..."
