@echo off
setlocal
REM ---- EDIT THESE TWO LINES ----
set MONTH=Jan 2026
set INPUT=Input\Jan 2026
REM ------------------------------

if not exist "%INPUT%" (
  echo Input folder not found: %INPUT%
  pause
  exit /b 1
)

py -3 make_reports.py --input "%INPUT%" --month "%MONTH%" --output "Output" --strict
echo.
pause
