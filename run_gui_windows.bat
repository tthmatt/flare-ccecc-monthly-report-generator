@echo off
setlocal
py -3 gui_app.py
if errorlevel 1 (
  echo.
  echo If this failed because Python packages are missing, run:
  echo py -m pip install -r requirements.txt
)
echo.
pause
