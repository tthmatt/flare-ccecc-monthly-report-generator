@echo off
setlocal
echo Starting Monthly Photo Report Generator web app...
py -3 -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Could not install required Python packages automatically.
  pause
  exit /b 1
)
start "" http://127.0.0.1:5000
py -3 web_app.py
if errorlevel 1 (
  echo.
  echo The web app could not start.
)
echo.
pause
