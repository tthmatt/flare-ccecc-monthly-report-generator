#!/bin/bash
set -e
echo "Starting Monthly Photo Report Generator web app..."
python3 -m pip install -r requirements.txt
python3 - <<'PY'
import webbrowser
webbrowser.open('http://127.0.0.1:5000')
PY
python3 web_app.py || {
  echo ""
  echo "The web app could not start."
}
echo ""
read -p "Press enter to exit..."
